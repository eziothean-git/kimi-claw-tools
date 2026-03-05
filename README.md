# Kimi Claw Tools

Kimi Claw's automation tools for RL locomotion research tracking.

## 工具列表

### 1. Paper Intelligence Analyzer (`src/paper_analyzer.py`)
- ✅ 自动分析ArXiv论文的核心贡献
- ✅ 基于关键词的相关性评分（0-100分）
- 🔄 LLM深度分析（开发中）

### 2. ArXiv Tracker (`src/arxiv_tracker.py`)
- ✅ 14个关键词自动抓取
- ✅ 智能去重数据库
- ✅ Tier-1/2实验室检测

### 3. Daily Report Generator (`src/generate_rl_report.sh`)
- ✅ GitHub仓库动态追踪
- ✅ 论文推送 + 相关性分析
- ✅ 多板块领域动态

### 4. Weekly Report Generator (Planned)
- ⏳ 周报自动生成
- ⏳ 趋势分析

## 开发计划

- [x] Phase 1: 论文智能分析（基础相关性评分）
- [x] Phase 2: 集成到每日报告
- [ ] Phase 3: LLM深度论文分析
- [ ] Phase 4: 周报自动生成
- [ ] Phase 5: Web仪表盘

## 运行时间

每日 00:00-08:00 (Asia/Shanghai) 自动执行

## 最近更新

- 2026-03-06: 初始化项目，添加论文分析器
- 2026-03-06: 相关性评分算法上线（7篇高度相关论文检出）
