# ChatGPT to Obsidian 整理系统

自动整理 ChatGPT 对话记录为 Obsidian 格式的笔记系统。

## 功能

- 📥 自动解析 ChatGPT 导出的 JSON 文件
- 🏷️ 智能分类（灵感/问题/代码/学习/项目/研究）
- 💡 提取关键洞察（代码块、问题、重要回答）
- 📝 生成 Obsidian 格式的 Markdown 文档
- 📋 自动生成索引和统计

## 使用方法

### 1. 导出 ChatGPT 数据

1. 打开 ChatGPT 网页
2. Settings → Data Controls → Export Data
3. 点击 Export，等待邮件（约 10-20 分钟）
4. 下载并解压，将 `conversations.json` 放入:
   ```
   /root/.openclaw/workspace/chatgpt_raw/
   ```

### 2. 运行整理脚本

```bash
python3 /tmp/kimi-claw-tools/src/chatgpt_manager.py
```

### 3. 查看结果

生成的 Obsidian Vault 位置:
```
/root/.openclaw/workspace/obsidian_vault/
```

目录结构:
```
obsidian_vault/
├── 索引.md              # 总索引和统计
├── 灵感/                # 灵感相关对话
├── 问题/                # 问题/疑问对话
├── 代码/                # 编程相关对话
├── 学习/                # 学习笔记对话
├── 项目/                # 项目讨论对话
├── 研究/                # 研究/论文对话
└── 其他/                # 未分类对话
```

## Obsidian 文档格式

每个对话生成一个 Markdown 文件，包含:

```yaml
---
title: "对话标题"
date: 2025-03-04 15:20
tags: ["问题", "项目"]
conversation_id: conv_1234567890
---
```

文档结构:
- 💡 关键洞察（自动提取）
- 📝 完整对话（可折叠）
- ✅ 行动项（待办清单）

## 自动化建议

可以设置 cron 定期自动整理:
```bash
# 每天凌晨2点自动整理
0 2 * * * python3 /tmp/kimi-claw-tools/src/chatgpt_manager.py
```

## 配置

编辑 `chatgpt_manager.py` 中的 `CONFIG` 修改:
- 分类标签和关键词
- 输入/输出目录
- 提取规则
