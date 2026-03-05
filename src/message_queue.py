#!/usr/bin/env python3
"""
Message Queue System for OpenClaw
解决并行Agent输出混乱问题
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

# 配置
QUEUE_DIR = Path("/root/.openclaw/workspace/message_queue")
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

class MessageQueue:
    """消息队列管理器"""
    
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.queue_file = QUEUE_DIR / f"queue_{user_id}.json"
        self.lock = threading.Lock()
        self._load_queue()
    
    def _load_queue(self):
        """加载队列状态"""
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                data = json.load(f)
                self.pending = deque(data.get('pending', []))
                self.processing = data.get('processing', None)
                self.history = data.get('history', [])
        else:
            self.pending = deque()
            self.processing = None
            self.history = []
    
    def _save_queue(self):
        """保存队列状态"""
        with open(self.queue_file, 'w') as f:
            json.dump({
                'pending': list(self.pending),
                'processing': self.processing,
                'history': self.history[-100:],  # 只保留最近100条
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
    
    def enqueue(self, message, source="kimi"):
        """添加消息到队列"""
        with self.lock:
            task = {
                'id': f"task_{int(time.time() * 1000)}",
                'message': message,
                'source': source,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            self.pending.append(task)
            self._save_queue()
            return task['id']
    
    def dequeue(self):
        """取出下一个待处理任务"""
        with self.lock:
            if self.processing:
                return None  # 有任务正在处理
            
            if not self.pending:
                return None
            
            task = self.pending.popleft()
            self.processing = task
            task['status'] = 'processing'
            task['started_at'] = datetime.now().isoformat()
            self._save_queue()
            return task
    
    def complete(self, task_id, result):
        """完成任务"""
        with self.lock:
            if self.processing and self.processing['id'] == task_id:
                self.processing['status'] = 'completed'
                self.processing['result'] = result
                self.processing['completed_at'] = datetime.now().isoformat()
                self.history.append(self.processing)
                self.processing = None
                self._save_queue()
                return True
            return False
    
    def fail(self, task_id, error):
        """标记任务失败"""
        with self.lock:
            if self.processing and self.processing['id'] == task_id:
                self.processing['status'] = 'failed'
                self.processing['error'] = str(error)
                self.processing['failed_at'] = datetime.now().isoformat()
                self.history.append(self.processing)
                self.processing = None
                self._save_queue()
                return True
            return False
    
    def get_status(self):
        """获取队列状态"""
        return {
            'pending_count': len(self.pending),
            'processing': self.processing,
            'total_history': len(self.history)
        }


class TaskManager:
    """任务管理器 - 汇总操作信息后发送"""
    
    def __init__(self, user_id="default"):
        self.queue = MessageQueue(user_id)
        self.current_task = None
        self.operations = []
        
    def start_task(self, message):
        """开始新任务"""
        # 检查是否有正在处理的任务
        status = self.queue.get_status()
        if status['processing']:
            # 添加到队列等待
            task_id = self.queue.enqueue(message)
            return {
                'status': 'queued',
                'task_id': task_id,
                'position': len(self.queue.pending),
                'message': f'任务已加入队列，当前位置: {len(self.queue.pending)}'
            }
        
        # 直接开始处理
        task = self.queue.dequeue()
        if task:
            self.current_task = task
            self.operations = []
            return {
                'status': 'processing',
                'task_id': task['id'],
                'message': '开始处理任务'
            }
        
        # 创建新任务
        task_id = self.queue.enqueue(message)
        return self.start_task(message)  # 递归调用开始处理
    
    def add_operation(self, operation_type, details):
        """记录操作步骤"""
        if self.current_task:
            self.operations.append({
                'type': operation_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
    
    def complete_task(self, final_result):
        """完成任务并生成汇总"""
        if not self.current_task:
            return None
        
        # 生成操作汇总
        summary = self._generate_summary()
        
        # 完成任务
        result = {
            'summary': summary,
            'final_result': final_result,
            'operations_count': len(self.operations),
            'duration': self._calculate_duration()
        }
        
        self.queue.complete(self.current_task['id'], result)
        self.current_task = None
        self.operations = []
        
        return result
    
    def _generate_summary(self):
        """生成操作汇总"""
        if not self.operations:
            return "无中间操作"
        
        summary_parts = []
        for i, op in enumerate(self.operations, 1):
            summary_parts.append(f"{i}. {op['type']}: {op['details']}")
        
        return "\n".join(summary_parts)
    
    def _calculate_duration(self):
        """计算任务耗时"""
        if self.current_task and 'started_at' in self.current_task:
            start = datetime.fromisoformat(self.current_task['started_at'])
            return (datetime.now() - start).total_seconds()
        return 0
    
    def get_queue_status(self):
        """获取队列状态报告"""
        status = self.queue.get_status()
        return f"""📊 任务队列状态

- 待处理: {status['pending_count']} 个任务
- 处理中: {'是' if status['processing'] else '否'}
- 历史记录: {status['total_history']} 个任务
"""


# 全局任务管理器实例
task_managers = {}

def get_task_manager(user_id="default"):
    """获取或创建任务管理器"""
    if user_id not in task_managers:
        task_managers[user_id] = TaskManager(user_id)
    return task_managers[user_id]


if __name__ == "__main__":
    # 测试
    tm = get_task_manager("test_user")
    
    # 添加任务
    result = tm.start_task("测试任务1")
    print(f"任务状态: {result}")
    
    # 记录操作
    tm.add_operation("读取文件", "读取了 config.json")
    tm.add_operation("执行命令", "执行了 git status")
    
    # 完成
    final = tm.complete_task("任务完成结果")
    print(f"\n完成结果:")
    print(f"汇总:\n{final['summary']}")
    print(f"操作数: {final['operations_count']}")
