#!/usr/bin/env python3
"""
LLM Paper Deep Analyzer
使用LLM（通过Copilot/GitHub API）深度分析论文
提取核心贡献、方法细节、实验结果和与你研究的关联
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 配置
PAPERS_DB_PATH = "/root/.openclaw/workspace/reports/arxiv_papers_db.json"
ANALYSIS_DB_PATH = "/root/.openclaw/workspace/reports/llm_paper_analysis.json"

# 用户研究背景（用于LLM分析上下文）
USER_CONTEXT = """
用户背景：
- 开发机器人运控RL框架 (Ezio's RL_ToolBox)
- 基于Instinct Lab / Isaac Lab架构
- 当前项目：CNHK ROSE Team人形机器人遥操
- 技术栈：Isaac Gym/Lab, MuJoCo, ROS2
- 核心痛点：Simulator API统一、Train/Deploy分离、Asset化管理
- 关注方向：Sim2Real, World Model, Transformer for Robotics, Continual Learning
"""


def load_papers_db():
    """加载论文数据库"""
    if os.path.exists(PAPERS_DB_PATH):
        with open(PAPERS_DB_PATH, 'r') as f:
            return json.load(f)
    return {"papers": []}


def load_llm_analysis_db():
    """加载LLM分析数据库"""
    if os.path.exists(ANALYSIS_DB_PATH):
        with open(ANALYSIS_DB_PATH, 'r') as f:
            return json.load(f)
    return {"analyses": {}}


def save_llm_analysis_db(db):
    """保存LLM分析数据库"""
    os.makedirs(os.path.dirname(ANALYSIS_DB_PATH), exist_ok=True)
    with open(ANALYSIS_DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)


def build_analysis_prompt(paper):
    """构建LLM分析提示词"""
    return f"""请分析以下机器人/AI论文，并按照指定格式输出分析结果。

{USER_CONTEXT}

论文信息：
标题: {paper.get('title')}
作者: {paper.get('author_str')}
类别: {', '.join(paper.get('categories', []))}

摘要:
{paper.get('summary')}

请按以下格式输出分析：

## 一句话总结
（用一句话概括论文的核心贡献）

## 核心方法
- 方法名称：
- 关键技术：
- 创新点：

## 实验验证
- 实验环境：
- 主要结果：
- 与SOTA对比：

## 与Ezio研究的关联度
- 相关领域：
- 可直接借鉴的技术/思路：
- 建议阅读优先级（高/中/低）：

## 代码/资源可用性
- 是否提到开源代码：
- 项目链接（如有）：

## 批判性思考
- 局限性：
- 可改进方向：
"""


def mock_llm_analysis(paper):
    """
    模拟LLM分析结果
    实际部署时会调用GitHub Copilot API或Kimi API
    """
    # 基于论文内容的关键词匹配生成简单分析
    title = paper.get('title', '').lower()
    summary = paper.get('summary', '').lower()
    text = title + ' ' + summary
    
    # 简单相关性判断
    relevance = "低"
    if any(kw in text for kw in ['locomotion', 'walking', 'quadruped', 'humanoid']):
        relevance = "高"
    elif any(kw in text for kw in ['rl', 'reinforcement learning', 'robot']):
        relevance = "中"
    
    # 检测是否有代码
    has_code = 'code' in text or 'github' in text or 'open source' in text
    
    return {
        "one_line_summary": f"本文研究了{paper.get('title')[:50]}...",
        "core_method": {
            "name": "待LLM分析",
            "key_techniques": [],
            "innovation": "待分析"
        },
        "experiments": {
            "environment": "待分析",
            "results": "待分析",
            "sota_comparison": "待分析"
        },
        "relevance": {
            "score": relevance,
            "related_areas": [],
            "actionable_insights": [],
            "priority": relevance
        },
        "code_availability": {
            "has_code": has_code,
            "links": []
        },
        "critical_thinking": {
            "limitations": "待分析",
            "improvements": "待分析"
        },
        "analyzed_at": datetime.now().isoformat(),
        "status": "mock"  # 标记为模拟结果
    }


def analyze_papers_with_llm(papers, limit=5):
    """
    对论文进行LLM深度分析
    当前使用模拟，后续接入真实LLM API
    """
    db = load_llm_analysis_db()
    
    analyzed_count = 0
    for paper in papers[:limit]:
        uid = paper.get('uid')
        
        # 跳过已分析的论文
        if uid in db["analyses"] and db["analyses"][uid].get("status") != "mock":
            continue
        
        print(f"Analyzing: {paper.get('title')[:60]}...")
        
        # TODO: 调用真实LLM API
        # prompt = build_analysis_prompt(paper)
        # analysis = call_llm_api(prompt)
        
        analysis = mock_llm_analysis(paper)
        db["analyses"][uid] = analysis
        analyzed_count += 1
    
    save_llm_analysis_db(db)
    return analyzed_count


def generate_llm_report(top_n=3):
    """生成LLM分析报告"""
    db = load_llm_analysis_db()
    papers_db = load_papers_db()
    
    # 创建uid到论文的映射
    papers_map = {p['uid']: p for p in papers_db.get('papers', [])}
    
    lines = []
    lines.append("## 🧠 LLM深度论文分析")
    lines.append("")
    lines.append("_基于Kimi/LLM的论文核心贡献提取_")
    lines.append("")
    
    # 获取高优先级分析
    high_priority = [
        (uid, analysis) for uid, analysis in db["analyses"].items()
        if analysis.get("relevance", {}).get("priority") == "高"
    ]
    
    if high_priority:
        lines.append("### 🔥 高优先级论文深度解读")
        lines.append("")
        
        for uid, analysis in high_priority[:top_n]:
            paper = papers_map.get(uid, {})
            lines.append(format_llm_analysis(paper, analysis))
    else:
        lines.append("_暂无高优先级论文分析_")
    
    # 统计
    total_analyzed = len(db["analyses"])
    mock_count = len([a for a in db["analyses"].values() if a.get("status") == "mock"])
    
    lines.append("---")
    lines.append("")
    lines.append(f"📊 **分析统计**: 总计 {total_analyzed} 篇 | 模拟分析 {mock_count} 篇")
    lines.append("")
    lines.append("💡 *注意：当前使用模拟分析。接入LLM API后可获得深度解读。*")
    
    return '\n'.join(lines)


def format_llm_analysis(paper, analysis):
    """格式化LLM分析结果"""
    rel = analysis.get("relevance", {})
    exp = analysis.get("experiments", {})
    code = analysis.get("code_availability", {})
    
    return f"""
#### 📄 [{paper.get('title', 'N/A')}]({paper.get('link', '')})

**一句话总结**: {analysis.get('one_line_summary', 'N/A')}

**建议优先级**: 🔴 {rel.get('priority', 'N/A').upper()}

**核心方法**: {analysis.get('core_method', {}).get('name', 'N/A')}

**实验环境**: {exp.get('environment', 'N/A')}

**开源代码**: {'✅ 有' if code.get('has_code') else '❌ 未提及'}

---
"""


def main():
    """主函数"""
    print("=" * 50)
    print("LLM Paper Deep Analyzer")
    print("=" * 50)
    
    # 加载论文
    db = load_papers_db()
    papers = db.get("papers", [])
    
    if not papers:
        print("No papers found in database.")
        return
    
    print(f"Loaded {len(papers)} papers")
    
    # 分析论文（限制数量以节省预算）
    print("\nAnalyzing papers with LLM...")
    analyzed = analyze_papers_with_llm(papers, limit=5)
    print(f"Analyzed {analyzed} papers")
    
    # 生成报告
    report = generate_llm_report(top_n=3)
    report_path = "/root/.openclaw/workspace/reports/llm_analysis.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to {report_path}")
    print(f"Total LLM analyses in database: {len(load_llm_analysis_db().get('analyses', {}))}")


if __name__ == "__main__":
    main()
