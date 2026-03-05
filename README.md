# Kimi Claw Tools

Kimi Claw's automation tools for RL locomotion research tracking.

Developed during 00:00-08:00 (Asia/Shanghai) for Ezio's RL research.

## 工具列表

### 1. ArXiv Tracker (`src/arxiv_tracker.py`)
- ✅ 14个关键词自动抓取
- ✅ 智能去重数据库 (JSON)
- ✅ Tier-1/2实验室检测
- ✅ 机器人类别过滤 (cs.RO/LG/AI/SY)

### 2. Paper Intelligence Analyzer (`src/paper_analyzer.py`)
- ✅ 基于关键词的相关性评分（0-100分）
- ✅ 研究方向匹配算法
- ✅ 高/中/低三级分类

### 3. LLM Deep Analyzer (`src/llm_analyzer.py`)
- ✅ 论文深度分析框架
- 🔄 接入GitHub Copilot/Kimi API（开发中）
- 🔄 核心贡献提取
- 🔄 实验结果解读

### 4. Weekly Report Generator (`src/weekly_report.py`)
- ✅ 周趋势分析
- ✅ 热门关键词统计
- ✅ 论文类别分布
- ✅ Top 5必读推荐

### 5. Daily Report Generator (`src/generate_rl_report.sh`)
- ✅ GitHub仓库动态追踪
- ✅ 论文推送 + 相关性分析
- ✅ 多板块领域动态（人形/四足/Sim2Real等）

## 系统架构

```
ArXiv API → arxiv_tracker.py → 论文数据库 (JSON)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
            paper_analyzer.py  llm_analyzer.py  weekly_report.py
                    ↓               ↓               ↓
            相关性评分        深度分析          周报生成
                    └───────────────┴───────────────┘
                                    ↓
                          generate_rl_report.sh
                                    ↓
                              每日报告 (Markdown)
```

## 开发计划

- [x] Phase 1: ArXiv抓取 + 数据库
- [x] Phase 2: 相关性评分算法
- [x] Phase 3: 周报生成器
- [x] Phase 4: LLM分析框架
- [ ] Phase 5: 接入真实LLM API
- [ ] Phase 6: Web仪表盘
- [ ] Phase 7: 代码提交智能分析

## 运行时间

| 任务 | 时间 | 触发方式 |
|------|------|---------|
| 每日报告 | 09:00 Asia/Shanghai | Cron |
| 周报生成 | 周一 08:00 | GitHub Actions |
| LLM分析 | 按需/夜间 | 手动/自动 |

## 配置

### 用户研究画像 (用于相关性评分)

**主要方向**:
- Legged robot locomotion control
- Humanoid robot walking
- Quadruped locomotion
- RL for robotics

**技术兴趣**:
- Sim2Real, Domain randomization
- World models, Transformer policies
- Continual learning, RMA, PMTG

**当前项目**:
- Ezio's RL_ToolBox 框架开发
- CNHK ROSE Team 人形遥操

## 最近更新

- **2026-03-06**: 初始化项目，添加论文分析器
- **2026-03-06**: 相关性评分算法上线（7篇高度相关论文检出）
- **2026-03-06**: 周报生成器上线
- **2026-03-06**: LLM分析框架完成（待接入API）

## 预算控制

- Allegretto Plan 40% 预算用于LLM API调用
- 夜间执行（00:00-08:00）以节省日间资源
- 论文分析限制数量，优先高相关性论文

---

🤖 _Built by Kimi Claw for Ezio's RL research journey_
