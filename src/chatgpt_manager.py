#!/usr/bin/env python3
"""
ChatGPT Conversation Manager
自动整理 ChatGPT 对话记录为 Obsidian 文档
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 配置
CONFIG = {
    "raw_export_dir": "/root/.openclaw/workspace/chatgpt_raw",
    "obsidian_vault_dir": "/root/.openclaw/workspace/obsidian_vault",
    "processed_dir": "/root/.openclaw/workspace/chatgpt_processed",
    "tags": {
        "灵感": ["idea", "灵感", "创意", "设想"],
        "问题": ["question", "问题", "疑问", "怎么", "如何"],
        "代码": ["code", "代码", "programming", "编程", "script"],
        "学习": ["learn", "学习", "study", "教程", "理解"],
        "项目": ["project", "项目", "实现", "开发", "build"],
        "研究": ["research", "研究", "论文", "文献", "paper"],
    }
}


def load_conversations(export_file):
    """加载 ChatGPT 导出的 JSON 文件"""
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conversations = []
    for conv in data.get('conversations', []):
        conv_data = {
            'id': conv.get('id'),
            'title': conv.get('title', 'Untitled'),
            'create_time': conv.get('create_time'),
            'update_time': conv.get('update_time'),
            'messages': []
        }
        
        for msg in conv.get('mapping', {}).values():
            if msg and 'message' in msg and msg['message']:
                message = msg['message']
                conv_data['messages'].append({
                    'role': message.get('author', {}).get('role'),
                    'content': message.get('content', {}).get('parts', [''])[0],
                    'timestamp': message.get('create_time')
                })
        
        conversations.append(conv_data)
    
    return conversations


def classify_conversation(conv):
    """根据内容分类对话"""
    text = ' '.join([m['content'] for m in conv['messages']]).lower()
    categories = []
    
    for category, keywords in CONFIG['tags'].items():
        if any(kw in text for kw in keywords):
            categories.append(category)
    
    return categories if categories else ['其他']


def extract_insights(conv):
    """提取关键洞察"""
    insights = []
    
    for msg in conv['messages']:
        content = msg['content']
        
        # 提取代码块
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            insights.append({
                'type': 'code',
                'content': f"Found {len(code_blocks)} code blocks"
            })
        
        # 提取关键问题
        if msg['role'] == 'user':
            questions = re.findall(r'[^.!?]*(?:怎么|如何|什么|为什么|是否)[^.!?]*[.!?]', content)
            if questions:
                insights.append({
                    'type': 'question',
                    'content': questions[0][:100]
                })
        
        # 提取 AI 的重要回答（较长且结构化的）
        if msg['role'] == 'assistant' and len(content) > 500:
            insights.append({
                'type': 'key_answer',
                'content': content[:200] + '...'
            })
    
    return insights


def generate_obsidian_note(conv, categories, insights):
    """生成 Obsidian 格式的 Markdown 文档"""
    
    # 格式化时间
    create_date = datetime.fromtimestamp(conv['create_time']).strftime('%Y-%m-%d %H:%M')
    
    # 生成 frontmatter
    tags_str = ', '.join([f'"{c}"' for c in categories])
    frontmatter = f"""---
title: "{conv['title']}"
date: {create_date}
tags: [{tags_str}]
conversation_id: {conv['id']}
---

"""
    
    # 生成内容摘要
    summary = f"""# {conv['title']}

> 📅 创建时间: {create_date}
> 🏷️ 分类: {', '.join(categories)}

## 💡 关键洞察

"""
    
    for insight in insights[:5]:  # 最多显示5个洞察
        if insight['type'] == 'code':
            summary += f"- 💻 {insight['content']}\n"
        elif insight['type'] == 'question':
            summary += f"- ❓ {insight['content']}\n"
        elif insight['type'] == 'key_answer':
            summary += f"- ✨ {insight['content']}\n"
    
    summary += "\n## 📝 对话记录\n\n"
    
    # 添加完整对话（折叠）
    summary += "<details>\n<summary>点击查看完整对话</summary>\n\n"
    
    for msg in conv['messages']:
        role = "👤 User" if msg['role'] == 'user' else "🤖 Assistant"
        summary += f"### {role}\n\n{msg['content']}\n\n"
    
    summary += "</details>\n"
    
    # 添加行动项
    summary += """\n## ✅ 行动项

- [ ] 回顾并提取可执行的任务
- [ ] 将代码片段整理到代码库
- [ ] 记录学习到的新概念

"""
    
    return frontmatter + summary


def organize_into_vault(conversations):
    """整理对话到 Obsidian Vault"""
    vault_dir = Path(CONFIG['obsidian_vault_dir'])
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    # 按类别创建目录
    for category in CONFIG['tags'].keys():
        (vault_dir / category).mkdir(exist_ok=True)
    
    (vault_dir / '其他').mkdir(exist_ok=True)
    
    # 处理每个对话
    for conv in conversations:
        categories = classify_conversation(conv)
        insights = extract_insights(conv)
        
        note_content = generate_obsidian_note(conv, categories, insights)
        
        # 保存到主目录
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', conv['title'])[:50]
        filename = f"{conv['id'][:8]}_{safe_title}.md"
        
        # 保存到第一个分类目录
        primary_category = categories[0]
        note_path = vault_dir / primary_category / filename
        
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(note_content)
        
        print(f"✅ 已保存: {note_path}")


def generate_index(conversations):
    """生成索引文档"""
    vault_dir = Path(CONFIG['obsidian_vault_dir'])
    
    # 按日期统计
    by_date = defaultdict(int)
    by_category = defaultdict(int)
    
    for conv in conversations:
        date = datetime.fromtimestamp(conv['create_time']).strftime('%Y-%m-%d')
        by_date[date] += 1
        
        categories = classify_conversation(conv)
        for cat in categories:
            by_category[cat] += 1

    # 生成索引内容
    index_content = f"""# ChatGPT 对话索引

> 自动生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 统计概览

- **总对话数**: {len(conversations)}
- **分类数量**: {len(by_category)}

### 按类别分布

| 类别 | 数量 |
|------|------|
"""
    
    for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        index_content += f"| [[{cat}]] | {count} |\n"
    
    index_content += """\n### 最近活动

| 日期 | 对话数 |
|------|--------|
"""
    
    for date, count in sorted(by_date.items(), reverse=True)[:10]:
        index_content += f"| {date} | {count} |\n"
    
    index_content += """\n## 🔍 快速导航

"""
    
    for category in CONFIG['tags'].keys():
        index_content += f"- [[{category}/]] - 查看所有 {category} 相关对话\n"
    
    # 保存索引
    with open(vault_dir / '索引.md', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"✅ 索引已生成: {vault_dir / '索引.md'}")


def main():
    """主函数"""
    print("=" * 50)
    print("ChatGPT Conversation Manager")
    print("=" * 50)
    
    # 查找最新的导出文件
    raw_dir = Path(CONFIG['raw_export_dir'])
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    export_files = list(raw_dir.glob('*.json'))
    
    if not export_files:
        print(f"\n⚠️ 未找到导出文件")
        print(f"请将 ChatGPT 导出的 JSON 文件放入: {raw_dir}")
        print("\n导出方法:")
        print("1. 打开 ChatGPT 网页")
        print("2. Settings > Data Controls > Export Data")
        print("3. 等待邮件并下载")
        print("4. 解压后将 conversations.json 放入上述目录")
        return
    
    # 使用最新的文件
    latest_file = max(export_files, key=lambda p: p.stat().st_mtime)
    print(f"\n📂 正在处理: {latest_file}")
    
    # 加载对话
    conversations = load_conversations(latest_file)
    print(f"✅ 加载了 {len(conversations)} 个对话")
    
    # 整理到 Obsidian Vault
    print("\n🗂️  正在整理到 Obsidian Vault...")
    organize_into_vault(conversations)
    
    # 生成索引
    print("\n📋 正在生成索引...")
    generate_index(conversations)
    
    print("\n" + "=" * 50)
    print(f"✅ 完成! Obsidian Vault 位置:")
    print(f"   {CONFIG['obsidian_vault_dir']}")
    print("=" * 50)


if __name__ == '__main__':
    main()
