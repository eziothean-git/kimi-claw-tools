#!/usr/bin/env python3
"""
Weekly Report Generator
汇总一周的研究动态，生成趋势分析和可视化
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path

# 配置
REPORTS_DIR = "/root/.openclaw/workspace/reports"
OUTPUT_DIR = "/root/.openclaw/workspace/reports/weekly"


def load_papers_from_week(days=7):
    """加载最近N天的论文数据"""
    db_path = os.path.join(REPORTS_DIR, "arxiv_papers_db.json")
    if not os.path.exists(db_path):
        return []
    
    with open(db_path, 'r') as f:
        db = json.load(f)
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent_papers = [
        p for p in db.get("papers", [])
        if p.get("published", '') >= cutoff_date or p.get("discovered_date", '') >= cutoff_date
    ]
    
    return recent_papers


def load_analysis_from_week(days=7):
    """加载最近N天的论文分析数据"""
    analysis_path = os.path.join(REPORTS_DIR, "paper_analysis.json")
    if not os.path.exists(analysis_path):
        return []
    
    with open(analysis_path, 'r') as f:
        data = json.load(f)
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    analyses = data.get("analyses", [])
    
    # 过滤最近的数据（简化处理，实际应该用analysis_timestamp）
    return analyses


def analyze_trends(papers):
    """分析研究趋势"""
    if not papers:
        return {}
    
    # 统计类别
    categories = []
    for p in papers:
        categories.extend(p.get("categories", []))
    category_counts = Counter(categories)
    
    # 提取关键词（简单版本）
    keywords = []
    for p in papers:
        text = (p.get("title", "") + " " + p.get("summary", "")).lower()
        interest_keywords = [
            "locomotion", "walking", "quadruped", "humanoid", "sim2real",
            "reinforcement learning", "rl", "policy", "control",
            "domain randomization", "world model", "transformer",
            "imitation learning", "teleoperation"
        ]
        for kw in interest_keywords:
            if kw in text:
                keywords.append(kw)
    keyword_counts = Counter(keywords)
    
    return {
        "categories": dict(category_counts.most_common(10)),
        "keywords": dict(keyword_counts.most_common(10)),
        "total_papers": len(papers)
    }


def generate_trend_chart(trends):
    """生成趋势文本图表"""
    lines = []
    
    # 关键词趋势
    lines.append("### 🔥 本周热门关键词")
    lines.append("")
    if trends.get("keywords"):
        max_count = max(trends["keywords"].values())
        for kw, count in trends["keywords"].items():
            bar = "█" * int(count / max_count * 20)
            lines.append(f"- `{kw}`: {bar} ({count})")
    else:
        lines.append("_暂无数据_")
    lines.append("")
    
    # 类别分布
    lines.append("### 📊 论文类别分布")
    lines.append("")
    if trends.get("categories"):
        for cat, count in trends["categories"].items():
            lines.append(f"- {cat}: {count}篇")
    else:
        lines.append("_暂无数据_")
    lines.append("")
    
    return '\n'.join(lines)


def generate_weekly_summary(analyses):
    """生成一周论文摘要"""
    if not analyses:
        return "_本周无论文数据_"
    
    # 按相关性排序
    sorted_analyses = sorted(analyses, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    lines = []
    lines.append("### 🏆 本周必读论文 Top 5")
    lines.append("")
    
    for analysis in sorted_analyses[:5]:
        score = analysis.get("relevance_score", 0)
        title = analysis.get("paper_title", "N/A")
        link = analysis.get("paper_link", "")
        keywords = ', '.join(analysis.get("keywords_matched", [])[:3])
        
        emoji = "🔥" if score >= 80 else "✅" if score >= 60 else "📄"
        lines.append(f"{emoji} **[{title}]({link})** — {score}分")
        if keywords:
            lines.append(f"   关键词: {keywords}")
        lines.append("")
    
    return '\n'.join(lines)


def generate_github_summary():
    """生成GitHub提交摘要"""
    # 这里简化处理，实际应该读取每日报告的历史数据
    return """### 💻 代码提交动态

_本周代码提交摘要将在后续版本中完善_

计划添加：
- 各仓库提交数量统计
- 代码变更热力图
- 主要功能开发进度
"""


def generate_weekly_report():
    """生成完整周报"""
    # 确定周报时间范围
    today = datetime.now()
    week_start = today - timedelta(days=7)
    week_end = today
    
    week_range = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
    
    # 加载数据
    papers = load_papers_from_week(7)
    analyses = load_analysis_from_week(7)
    trends = analyze_trends(papers)
    
    # 构建报告
    lines = []
    lines.append(f"# 📊 运控RL周报 ({week_range})")
    lines.append("")
    lines.append(f"_汇总周期: {week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}_")
    lines.append("")
    
    # 统计数据
    lines.append("## 📈 数据概览")
    lines.append("")
    lines.append(f"- **新增论文**: {len(papers)} 篇")
    lines.append(f"- **高度相关论文** (≥70分): {len([a for a in analyses if a.get('relevance_score', 0) >= 70])} 篇")
    lines.append(f"- **中度相关论文** (40-69分): {len([a for a in analyses if 40 <= a.get('relevance_score', 0) < 70])} 篇")
    lines.append("")
    
    # 趋势分析
    lines.append("## 📊 研究趋势分析")
    lines.append("")
    lines.append(generate_trend_chart(trends))
    
    # 必读论文
    lines.append("## 🏆 本周精选论文")
    lines.append("")
    lines.append(generate_weekly_summary(analyses))
    
    # GitHub动态
    lines.append("## 💻 开发动态")
    lines.append("")
    lines.append(generate_github_summary())
    
    # 下周预告
    lines.append("## 🔮 下周关注")
    lines.append("")
    lines.append("- [ ] 持续跟踪人形机器人运控新论文")
    lines.append("- [ ] 监控Transformer for Robotics进展")
    lines.append("- [ ] 关注Sim2Real最新方法")
    lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("")
    lines.append(f"_周报生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")
    lines.append("🤖 _Generated by Kimi Claw_")
    
    return '\n'.join(lines)


def save_weekly_report(report_text):
    """保存周报"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    today = datetime.now()
    week_num = today.isocalendar()[1]
    filename = f"weekly_report_{today.year}_W{week_num:02d}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(report_text)
    
    return filepath


def main():
    """主函数"""
    print("=" * 50)
    print("Weekly Report Generator")
    print("=" * 50)
    
    # 生成周报
    report = generate_weekly_report()
    
    # 保存周报
    filepath = save_weekly_report(report)
    print(f"\nWeekly report saved to: {filepath}")
    
    # 打印摘要
    print("\nReport preview:")
    print("-" * 50)
    print(report[:500] + "...")


if __name__ == "__main__":
    main()
