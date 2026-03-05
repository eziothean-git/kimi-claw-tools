#!/usr/bin/env python3
"""
Response Aggregator for OpenClaw
聚合多个操作输出，汇总后一次性发送
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 配置
AGGREGATOR_DIR = Path("/root/.openclaw/workspace/response_aggregator")
AGGREGATOR_DIR.mkdir(parents=True, exist_ok=True)


class ResponseAggregator:
    """响应聚合器 - 汇总多个操作后统一输出"""
    
    def __init__(self, session_id="default"):
        self.session_id = session_id
        self.state_file = AGGREGATOR_DIR / f"session_{session_id}.json"
        self.reset()
    
    def reset(self):
        """重置状态"""
        self.sections = {
            'status': [],      # 状态信息
            'operations': [],  # 操作记录
            'results': [],     # 结果数据
            'errors': [],      # 错误信息
            'summary': []      # 总结信息
        }
        self.start_time = datetime.now()
        self._save_state()
    
    def _save_state(self):
        """保存状态"""
        with open(self.state_file, 'w') as f:
            json.dump({
                'sections': self.sections,
                'start_time': self.start_time.isoformat(),
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
    
    def add_status(self, message):
        """添加状态信息"""
        self.sections['status'].append({
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def add_operation(self, operation, details=""):
        """添加操作记录"""
        self.sections['operations'].append({
            'operation': operation,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def add_result(self, title, content):
        """添加结果"""
        self.sections['results'].append({
            'title': title,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def add_error(self, error):
        """添加错误"""
        self.sections['errors'].append({
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def add_summary(self, summary):
        """添加总结"""
        self.sections['summary'].append({
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        self._save_state()
    
    def generate_final_response(self):
        """生成最终汇总响应"""
        parts = []
        
        # 标题
        duration = (datetime.now() - self.start_time).total_seconds()
        parts.append(f"## 任务完成 (耗时: {duration:.1f}s)")
        parts.append("")
        
        # 状态信息
        if self.sections['status']:
            parts.append("### 📋 执行状态")
            for s in self.sections['status']:
                parts.append(f"- {s['message']}")
            parts.append("")
        
        # 操作记录
        if self.sections['operations']:
            parts.append("### 🔧 操作步骤")
            for i, op in enumerate(self.sections['operations'], 1):
                if op['details']:
                    parts.append(f"{i}. **{op['operation']}**: {op['details']}")
                else:
                    parts.append(f"{i}. **{op['operation']}**")
            parts.append("")
        
        # 结果展示
        if self.sections['results']:
            parts.append("### 📊 执行结果")
            for r in self.sections['results']:
                parts.append(f"\n**{r['title']}**:")
                parts.append(f"```\n{r['content']}\n```")
            parts.append("")
        
        # 错误信息
        if self.sections['errors']:
            parts.append("### ⚠️ 错误信息")
            for e in self.sections['errors']:
                parts.append(f"- ❌ {e['error']}")
            parts.append("")
        
        # 总结
        if self.sections['summary']:
            parts.append("### 📝 总结")
            for s in self.sections['summary']:
                parts.append(s['summary'])
            parts.append("")
        
        return "\n".join(parts)
    
    def finalize(self):
        """完成并返回最终响应"""
        response = self.generate_final_response()
        self.reset()  # 重置状态
        return response


# 全局聚合器实例
aggregators = {}

def get_aggregator(session_id="default"):
    """获取或创建聚合器"""
    if session_id not in aggregators:
        aggregators[session_id] = ResponseAggregator(session_id)
    return aggregators[session_id]


# 便捷函数
def start_session(session_id="default"):
    """开始新会话"""
    agg = get_aggregator(session_id)
    agg.reset()
    return agg

def add_operation(operation, details="", session_id="default"):
    """添加操作"""
    agg = get_aggregator(session_id)
    agg.add_operation(operation, details)

def add_result(title, content, session_id="default"):
    """添加结果"""
    agg = get_aggregator(session_id)
    agg.add_result(title, content)

def finalize_session(session_id="default"):
    """完成会话"""
    agg = get_aggregator(session_id)
    return agg.finalize()


if __name__ == "__main__":
    # 测试
    agg = start_session("test")
    
    agg.add_operation("读取配置", "加载 openclaw.json")
    agg.add_operation("验证API", "检查 Moonshot API 状态")
    agg.add_result("配置状态", "所有配置项验证通过")
    agg.add_summary("任务成功完成，无错误")
    
    print(agg.finalize())
