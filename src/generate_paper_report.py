#!/usr/bin/env python3
"""
Generate detailed paper report with neural network RL focus
"""
import json
import os
import urllib.request
from datetime import datetime

REPORT_DIR = "/root/.openclaw/workspace/reports"
PDF_DIR = f"{REPORT_DIR}/pdfs"
DB_PATH = f"{REPORT_DIR}/arxiv_papers_db.json"

def load_papers():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return {"papers": []}

def download_pdf(paper_id, title):
    """尝试下载PDF"""
    try:
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        safe_title = "".join(c for c in title[:30] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        pdf_path = f"{PDF_DIR}/{safe_title}.pdf"
        
        if os.path.exists(pdf_path):
            return pdf_path
            
        urllib.request.urlretrieve(pdf_url, pdf_path)
        return pdf_path
    except Exception as e:
        return None

def score_neural_rl_relevance(paper):
    """计算神经网络RL相关性"""
    text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
    score = 0
    
    keywords = [
        ("neural network", 30), ("deep reinforcement learning", 30),
        ("neural policy", 25), ("actor critic", 20),
        ("policy gradient", 20), ("deep rl", 20),
        ("value network", 15), ("q-network", 15),
        ("function approximation", 15), ("representation learning", 15),
    ]
    
    for kw, pts in keywords:
        if kw in text:
            score += pts
    
    return min(score, 100)

def extract_methods(text_lower):
    """提取方法论"""
    methods = []
    method_map = {
        'ppo': 'PPO', 'sac': 'SAC', 'td3': 'TD3',
        'actor-critic': 'Actor-Critic', 'a3c': 'A3C',
        'trpo': 'TRPO', 'ddpg': 'DDPG',
        'transformer': 'Transformer',
        'world model': 'World Model',
        'imitation': 'Imitation Learning',
        'meta learning': 'Meta Learning',
        'curiosity': 'Curiosity Driven',
    }
    for key, value in method_map.items():
        if key in text_lower:
            methods.append(value)
    return methods

def main():
    os.makedirs(PDF_DIR, exist_ok=True)
    
    db = load_papers()
    papers = db.get("papers", [])
    
    if not papers:
        print("未找到论文数据，请先运行 arxiv_tracker.py")
        return
    
    # 按神经网络RL相关性排序
    scored_papers = [(score_neural_rl_relevance(p), p) for p in papers]
    scored_papers.sort(key=lambda x: x[0], reverse=True)
    
    print("### 🔥 Top 5 神经网络强化学习论文\n")
    
    count = 0
    for score, paper in scored_papers[:10]:
        if count >= 5:
            break
        
        title = paper.get('title', 'N/A')
        summary = paper.get('summary', 'N/A')
        link = paper.get('link', '')
        paper_id = paper.get('id', '').split('/')[-1].replace('v1', '').replace('v2', '')
        
        # 提取arXiv ID
        arxiv_id = paper_id
        if 'arxiv.org' in paper.get('id', ''):
            arxiv_id = paper.get('id', '').split('/')[-1]
        
        print(f"#### {count+1}. [{title}]({link})")
        print(f"**神经网络RL相关性评分**: {score}/100")
        print(f"**发布时间**: {paper.get('published', 'N/A')}")
        print(f"**arXiv ID**: {arxiv_id}")
        print("")
        
        # 内容概括
        summary_short = summary[:300] + "..." if len(summary) > 300 else summary
        print("**📋 内容概括**:")
        print(f"> {summary_short}")
        print("")
        
        # 下载PDF
        pdf_path = download_pdf(arxiv_id, title)
        if pdf_path:
            print(f"**📥 PDF下载**: `{pdf_path}`")
        else:
            print(f"**📥 PDF下载**: [点击下载](https://arxiv.org/pdf/{arxiv_id}.pdf)")
        print("")
        
        # 关键要点
        print("**🔑 关键要点**:")
        text_lower = (title + ' ' + summary).lower()
        methods = extract_methods(text_lower)
        
        if methods:
            print(f"- **核心方法**: {', '.join(methods[:4])}")
        
        # 判断应用场景
        if 'humanoid' in text_lower or 'bipedal' in text_lower:
            print("- **应用场景**: 人形机器人控制")
        elif 'quadruped' in text_lower or 'legged' in text_lower:
            print("- **应用场景**: 四足/腿式机器人")
        elif 'manipulation' in text_lower:
            print("- **应用场景**: 机器人操作")
        else:
            print("- **应用场景**: 通用机器人RL")
        
        # 与ToolBox的关联
        if score >= 80:
            print("- **ToolBox相关性**: 🔴 高度相关，建议深入阅读")
        elif score >= 60:
            print("- **ToolBox相关性**: 🟡 中度相关，可作为参考")
        else:
            print("- **ToolBox相关性**: 🟢 低度相关，了解即可")
        
        print("")
        print("---")
        print("")
        
        count += 1
    
    print(f"\n📊 **论文统计**: 共分析 {len(papers)} 篇论文，精选 **{count}** 篇神经网络RL相关")
    print(f"📥 **PDF下载**: 已保存到 `{PDF_DIR}/` 目录")

if __name__ == "__main__":
    main()
