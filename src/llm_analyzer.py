#!/usr/bin/env python3
"""
LLM Paper Deep Analyzer - Using Kimi API (with fallback)
深度分析论文，提取核心贡献和与用户研究的关联
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

# 配置
REPORTS_DIR = "/root/.openclaw/workspace/reports"
PAPERS_DB_PATH = os.path.join(REPORTS_DIR, "arxiv_papers_db.json")
ANALYSIS_DB_PATH = os.path.join(REPORTS_DIR, "llm_paper_analysis.json")
LOGS_DIR = "/root/.openclaw/workspace/logs"

# 确保目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# 导入预算追踪
try:
    from budget_tracker import check_budget_status, record_usage
    BUDGET_TRACKING = True
except ImportError:
    BUDGET_TRACKING = False


def log_message(msg, level="INFO"):
    """记录日志到文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = os.path.join(LOGS_DIR, f'llm_analyzer_{datetime.now().strftime("%Y%m%d")}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{level}] {msg}\n")


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
    with open(ANALYSIS_DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)


def analyze_paper_with_kimi(paper):
    """使用Kimi API分析论文"""
    title = paper.get('title', '')
    abstract = paper.get('summary', '')
    authors = paper.get('author_str', '')
    
    # 构建提示词
    prompt = f"""作为机器人运控领域的研究助手，请深度分析以下论文：

【论文信息】
标题: {title}
作者: {authors}
类别: {', '.join(paper.get('categories', []))}

【摘要】
{abstract}

【分析要求】
请按以下结构提供分析（使用中文）：

1. 一句话总结：
用一句话概括核心贡献

2. 核心方法：
- 解决什么问题
- 关键技术/算法
- 与主流方法的区别

3. 实验验证：
- 仿真环境/真实机器人
- 主要结果指标
- 与SOTA对比

4. 与你研究的关联度（1-10分）：
考虑：是否与legged locomotion/RL/sim2real相关，是否可借鉴到Ezio's RL_ToolBox

5. 可借鉴的技术点：
列出可以直接应用或参考的思路

6. 代码/资源可用性：
是否提及开源代码、数据集链接

7. 局限性与改进方向：
"""
    
    log_message(f"Calling Kimi API for: {title[:50]}...")
    
    try:
        result_file = os.path.join(LOGS_DIR, 'last_kimi_result.txt')
        
        cmd = [
            'python3', '/tmp/kimi-claw-tools/src/kimi_code.py',
            'ask',
            '--prompt', prompt,
            '--output', result_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            log_message(f"Kimi API call failed: {result.stderr}", "ERROR")
            return None
        
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                response = f.read()
            if response and not response.startswith('Error'):
                log_message(f"Kimi API response received, length: {len(response)}")
                return response
            else:
                log_message(f"Kimi API returned error: {response}", "ERROR")
                return None
        else:
            log_message("No result file generated", "ERROR")
            return None
            
    except Exception as e:
        log_message(f"Kimi API error: {str(e)}", "ERROR")
        return None


def mock_llm_analysis(paper):
    """模拟LLM分析（API不可用时使用）"""
    title = paper.get('title', '')
    summary = paper.get('summary', '')
    text = (title + ' ' + summary).lower()
    
    # 基于关键词的简单分析
    relevance_score = 5
    if any(kw in text for kw in ['locomotion', 'walking', 'quadruped', 'humanoid']):
        relevance_score = 8
    if 'reinforcement learning' in text or 'rl' in text:
        relevance_score += 1
    if 'sim2real' in text:
        relevance_score += 1
    
    relevance_score = min(relevance_score, 10)
    
    priority = "高" if relevance_score >= 8 else "中" if relevance_score >= 5 else "低"
    
    return f"""1. 一句话总结：
本文研究了{title[:50]}...（模拟分析）

2. 核心方法：
- 问题：待详细分析
- 技术：基于论文摘要，涉及{', '.join(paper.get('categories', ['unknown'])[:2])}
- 创新：待详细分析

3. 实验验证：
- 环境：待确认
- 结果：待提取
- 对比：待对比

4. 与你研究的关联度（{relevance_score}/10）：
基于关键词匹配（locomotion/RL/sim2real）的初步评估

5. 可借鉴的技术点：
- 需详细阅读后确定

6. 代码/资源可用性：
待检查论文中是否提及

7. 局限性与改进方向：
待详细分析

---
注意：此为模拟分析。API配置完成后将提供深度解读。
""", relevance_score, priority


def parse_analysis_response(response, paper, is_mock=False):
    """解析响应为结构化数据"""
    if not response:
        return None
    
    if is_mock:
        text, score, priority = response
        return {
            "full_analysis": text,
            "relevance_score": score,
            "priority": priority,
            "paper_title": paper.get('title'),
            "paper_link": paper.get('link'),
            "analyzed_at": datetime.now().isoformat(),
            "status": "mock"
        }
    
    # 尝试提取关联度分数
    relevance_score = 5
    try:
        import re
        match = re.search(r'关联度.*?([0-9]+)', response)
        if match:
            relevance_score = int(match.group(1))
        else:
            match = re.search(r'([0-9]+)/10', response)
            if match:
                relevance_score = int(match.group(1))
    except:
        pass
    
    priority = "高" if relevance_score >= 8 else "中" if relevance_score >= 5 else "低"
    
    return {
        "full_analysis": response,
        "relevance_score": relevance_score,
        "priority": priority,
        "paper_title": paper.get('title'),
        "paper_link": paper.get('link'),
        "analyzed_at": datetime.now().isoformat(),
        "status": "completed"
    }


def analyze_papers(papers, limit=3):
    """分析论文（带预算控制）"""
    # 检查预算
    if BUDGET_TRACKING:
        budget_status = check_budget_status()
        available_papers = budget_status["papers_available_today"]
        if available_papers <= 0:
            log_message("Daily budget exhausted, skipping LLM analysis", "WARN")
            return 0
        # 限制分析数量不超过预算允许
        limit = min(limit, available_papers)
        log_message(f"Budget check: {available_papers} papers available today, analyzing {limit}")
    
    db = load_llm_analysis_db()
    
    # 筛选高相关且未分析的论文
    candidates = []
    for paper in papers:
        uid = paper.get('uid')
        if uid not in db.get("analyses", {}):
            score = calculate_quick_score(paper)
            candidates.append((score, paper))
    
    candidates.sort(reverse=True, key=lambda x: x[0])
    
    analyzed_count = 0
    use_mock = False
    
    for score, paper in candidates[:limit]:
        uid = paper.get('uid')
        
        log_message(f"Analyzing paper (score {score}): {paper.get('title', '')[:60]}...")
        
        # 先尝试Kimi API
        response = analyze_paper_with_kimi(paper)
        is_mock = False
        
        if not response:
            # API失败，使用模拟
            log_message("API failed, using mock analysis")
            response = mock_llm_analysis(paper)
            is_mock = True
            use_mock = True
        
        if response:
            analysis = parse_analysis_response(response, paper, is_mock=is_mock)
            if analysis:
                db.setdefault("analyses", {})[uid] = analysis
                analyzed_count += 1
                
                # 记录预算使用
                if BUDGET_TRACKING and not is_mock:
                    record_usage(3000, 1500, f"Paper analysis: {paper.get('title', '')[:50]}...")
                
                log_message(f"Analysis completed for {paper.get('title', '')[:60]}...")
    
    save_llm_analysis_db(db)
    
    if use_mock:
        log_message("Note: Using mock analysis due to API unavailability", "WARN")
    
    return analyzed_count


def calculate_quick_score(paper):
    """快速计算相关性分数"""
    text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
    score = 0
    
    keywords = [
        ("locomotion", 20), ("walking", 20), ("quadruped", 20), ("humanoid", 20),
        ("reinforcement learning", 15), ("rl ", 15), ("policy", 10),
        ("sim2real", 15), ("domain randomization", 10),
        ("tendon", 10), ("exoskeleton", 10),
        ("isaac", 10), ("mujoco", 10),
    ]
    
    for kw, pts in keywords:
        if kw in text:
            score += pts
    
    return min(score, 100)


def generate_llm_report(top_n=3):
    """生成LLM分析报告"""
    db = load_llm_analysis_db()
    papers_db = load_papers_db()
    papers_map = {p['uid']: p for p in papers_db.get('papers', [])}
    
    lines = []
    lines.append("## 🔬 LLM深度论文分析")
    lines.append("")
    lines.append("_基于Kimi K2.5的深度解读_")
    lines.append("")
    
    analyses = []
    for uid, analysis in db.get("analyses", {}).items():
        analyses.append((analysis.get("relevance_score", 0), uid, analysis))
    
    analyses.sort(reverse=True)
    
    if analyses:
        lines.append(f"### 📊 本周深度分析 ({len(analyses)}篇)")
        lines.append("")
        
        for score, uid, analysis in analyses[:top_n]:
            paper = papers_map.get(uid, {})
            is_mock = analysis.get("status") == "mock"
            emoji = "🔥" if score >= 8 else "✅" if score >= 5 else "📄"
            mock_tag = " [模拟]" if is_mock else ""
            
            lines.append(f"#### {emoji} [{analysis.get('paper_title', 'N/A')}]({analysis.get('paper_link', '')}){mock_tag}")
            lines.append("")
            lines.append(f"**关联度评分**: {score}/10 | **建议优先级**: {analysis.get('priority', 'N/A')}")
            lines.append("")
            
            full_text = analysis.get('full_analysis', '')
            summary = '\n'.join(full_text.split('\n')[:15])
            lines.append(summary)
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("_暂无LLM分析数据_")
        lines.append("")
    
    total = len(db.get("analyses", {}))
    completed = len([a for a in db.get("analyses", {}).values() if a.get("status") == "completed"])
    mock_count = len([a for a in db.get("analyses", {}).values() if a.get("status") == "mock"])
    
    lines.append(f"📊 **分析统计**: 总计 {total} 篇 | 真实API {completed} 篇 | 模拟 {mock_count} 篇")
    lines.append("")
    
    if mock_count > 0:
        lines.append("⚠️ *部分分析使用模拟数据。API配置完成后将提供真实深度解读。*")
    else:
        lines.append("💡 *每篇分析消耗约2-4K tokens*")
    
    return '\n'.join(lines)


def main():
    """主函数"""
    log_message("=" * 50)
    log_message("LLM Paper Deep Analyzer Started")
    log_message("=" * 50)
    
    db = load_papers_db()
    papers = db.get("papers", [])
    
    if not papers:
        log_message("No papers found in database")
        return
    
    log_message(f"Loaded {len(papers)} papers from database")
    
    log_message("Starting paper analysis...")
    analyzed = analyze_papers(papers, limit=3)
    log_message(f"Analyzed {analyzed} papers")
    
    report = generate_llm_report(top_n=3)
    report_path = os.path.join(REPORTS_DIR, "llm_analysis.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    log_message(f"Report saved to {report_path}")
    log_message("=" * 50)


if __name__ == "__main__":
    main()
