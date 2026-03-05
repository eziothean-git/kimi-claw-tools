#!/usr/bin/env python3
"""
Paper Intelligence Analyzer
使用LLM自动分析ArXiv论文，提取核心贡献和与你的研究的相关性
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置
PAPERS_DB_PATH = "/root/.openclaw/workspace/reports/arxiv_papers_db.json"
ANALYSIS_OUTPUT_PATH = "/root/.openclaw/workspace/reports/paper_analysis.json"
DAILY_REPORT_DIR = "/root/.openclaw/workspace/reports"

# 用户的研究方向（用于相关性评估）
USER_RESEARCH_PROFILE = {
    "primary_focus": [
        "legged robot locomotion control",
        "humanoid robot walking",
        "quadruped locomotion",
        "reinforcement learning for robotics"
    ],
    "technical_interests": [
        "sim2real transfer",
        "domain randomization",
        "world models for robotics",
        "transformer policies",
        "continual learning",
        "teacher-student distillation",
        "rapid motor adaptation (RMA)",
        "whole-body control",
        "reward function design",
        "Isaac Lab/Gym simulation"
    ],
    "current_projects": [
        "RL framework development (Ezio's RL_ToolBox)",
        "CNHK ROSE Team humanoid teleoperation",
        "Compat Layer abstraction for multi-backend sim"
    ],
    "preferred_methods": [
        "PPO", "AMP", "TPPO", "RMA", "PMTG", "NPMP"
    ]
}


def load_papers_db():
    """加载论文数据库"""
    if os.path.exists(PAPERS_DB_PATH):
        with open(PAPERS_DB_PATH, 'r') as f:
            return json.load(f)
    return {"papers": [], "last_fetch": None}


def format_paper_for_analysis(paper):
    """格式化论文信息供LLM分析"""
    return f"""
Title: {paper.get('title', 'N/A')}
Authors: {paper.get('author_str', 'N/A')}
Categories: {', '.join(paper.get('categories', []))}
Published: {paper.get('published', 'N/A')}

Abstract:
{paper.get('summary', 'N/A')}
"""


def analyze_paper_with_llm(paper_text):
    """
    使用LLM分析论文
    注意：此函数在实际运行时会调用Kimi API
    现在返回模拟结果作为占位
    """
    # TODO: 集成Kimi API进行实际分析
    # 返回结构化分析模板
    return {
        "core_contribution": "待分析",
        "key_methods": ["待提取"],
        "experimental_validation": "待评估",
        "relevance_score": 0,  # 0-100
        "relevance_reasoning": "待评估",
        "technical_novelty": 0,  # 0-100
        "implementation_difficulty": "待评估",  # easy/medium/hard
        "recommended_action": "待决定",  # read/skim/skip
        "tags": []
    }


def calculate_relevance_score(paper, profile=USER_RESEARCH_PROFILE):
    """
    基于关键词匹配计算相关性分数
    这是一个启发式评分，后续可以用LLM改进
    """
    score = 0
    text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
    
    # 主要研究方向匹配 (+20 each)
    for focus in profile["primary_focus"]:
        if any(kw in text for kw in focus.lower().split()):
            score += 20
    
    # 技术兴趣匹配 (+10 each)
    for tech in profile["technical_interests"]:
        if any(kw in text for kw in tech.lower().split()):
            score += 10
    
    # 当前项目相关 (+15 each)
    for project_keyword in ["teleoperation", "humanoid", "framework", "compat"]:
        if project_keyword in text:
            score += 15
    
    # 方法论匹配 (+10 each)
    for method in profile["preferred_methods"]:
        if method.lower() in text:
            score += 10
    
    # 类别加分
    categories = paper.get('categories', [])
    if 'cs.RO' in categories:
        score += 15
    if 'cs.LG' in categories:
        score += 10
    
    return min(score, 100)  # 封顶100


def analyze_all_papers(papers=None, limit=None):
    """
    分析论文数据库中的所有论文
    
    Args:
        papers: 论文列表，如果为None则加载全部
        limit: 限制分析数量（用于测试）
    """
    if papers is None:
        db = load_papers_db()
        papers = db.get("papers", [])
    
    if limit:
        papers = papers[:limit]
    
    analyses = []
    
    for paper in papers:
        # 计算相关性分数
        relevance_score = calculate_relevance_score(paper)
        
        # 构建分析结果
        analysis = {
            "paper_uid": paper.get("uid"),
            "paper_title": paper.get("title"),
            "paper_link": paper.get("link"),
            "published": paper.get("published"),
            "relevance_score": relevance_score,
            "tier": "high" if relevance_score >= 70 else "medium" if relevance_score >= 40 else "low",
            "keywords_matched": extract_matched_keywords(paper),
            "analysis_timestamp": datetime.now().isoformat(),
            # LLM分析字段（后续填充）
            "llm_analysis": None
        }
        
        analyses.append(analysis)
    
    # 按相关性排序
    analyses.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return analyses


def extract_matched_keywords(paper):
    """提取匹配的关键词"""
    text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
    matched = []
    
    all_keywords = (
        USER_RESEARCH_PROFILE["primary_focus"] +
        USER_RESEARCH_PROFILE["technical_interests"] +
        USER_RESEARCH_PROFILE["preferred_methods"]
    )
    
    for keyword in all_keywords:
        if any(kw in text for kw in keyword.lower().split()):
            matched.append(keyword)
    
    return list(set(matched))[:5]  # 最多返回5个


def generate_analysis_report(analyses, top_n=10):
    """生成分析报告Markdown"""
    lines = []
    lines.append("## 🧠 论文智能分析")
    lines.append("")
    lines.append(f"_基于你的研究方向（运控RL / 人形机器人 / Sim2Real）的相关性评分_")
    lines.append("")
    
    # 高相关论文
    high_relevance = [a for a in analyses if a["tier"] == "high"][:top_n]
    if high_relevance:
        lines.append("### 🔥 高度相关论文 (Score ≥70)")
        lines.append("")
        for analysis in high_relevance:
            lines.append(format_analysis_entry(analysis))
        lines.append("")
    
    # 中等相关
    medium_relevance = [a for a in analyses if a["tier"] == "medium"][:5]
    if medium_relevance:
        lines.append("### 🔸 中度相关论文 (Score 40-69)")
        lines.append("")
        for analysis in medium_relevance:
            lines.append(format_analysis_entry(analysis, compact=True))
        lines.append("")
    
    # 统计
    lines.append("---")
    lines.append("")
    lines.append(f"📊 **分析统计**: 总计 {len(analyses)} 篇 | 高度相关 {len([a for a in analyses if a['tier']=='high'])} 篇 | 中度相关 {len([a for a in analyses if a['tier']=='medium'])} 篇")
    
    return '\n'.join(lines)


def format_analysis_entry(analysis, compact=False):
    """格式化单篇论文分析"""
    score_emoji = "🔥" if analysis["relevance_score"] >= 80 else "✅" if analysis["relevance_score"] >= 60 else "📄"
    
    if compact:
        return f"- {score_emoji} [{analysis['paper_title'][:60]}...]({analysis['paper_link']}) — **{analysis['relevance_score']}分**"
    
    keywords_str = ', '.join(analysis.get('keywords_matched', []))
    return f"""
### {score_emoji} [{analysis['paper_title']}]({analysis['paper_link']})

**相关性评分**: {analysis['relevance_score']}/100 | **发布时间**: {analysis['published']}

**匹配关键词**: {keywords_str}

---
"""


def save_analysis(analyses):
    """保存分析结果"""
    os.makedirs(os.path.dirname(ANALYSIS_OUTPUT_PATH), exist_ok=True)
    with open(ANALYSIS_OUTPUT_PATH, 'w') as f:
        json.dump({
            "analyses": analyses,
            "generated_at": datetime.now().isoformat(),
            "total_papers": len(analyses)
        }, f, indent=2)


def main():
    """主函数"""
    print("=" * 50)
    print("Paper Intelligence Analyzer")
    print("=" * 50)
    
    # 加载论文
    db = load_papers_db()
    papers = db.get("papers", [])
    
    if not papers:
        print("No papers found in database. Run arxiv_tracker.py first.")
        return
    
    print(f"Loaded {len(papers)} papers from database")
    
    # 分析论文
    print("Analyzing papers...")
    analyses = analyze_all_papers(papers, limit=None)
    
    # 保存分析结果
    save_analysis(analyses)
    print(f"Analysis saved to {ANALYSIS_OUTPUT_PATH}")
    
    # 生成报告
    report = generate_analysis_report(analyses)
    report_path = os.path.join(DAILY_REPORT_DIR, "paper_analysis.md")
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved to {report_path}")
    
    # 打印摘要
    high_count = len([a for a in analyses if a["tier"] == "high"])
    medium_count = len([a for a in analyses if a["tier"] == "medium"])
    print(f"\nSummary: {high_count} high relevance, {medium_count} medium relevance papers")


if __name__ == "__main__":
    main()
