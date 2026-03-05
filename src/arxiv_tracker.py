#!/usr/bin/env python3
"""
ArXiv Paper Tracker for RL Locomotion
- Fetches daily papers based on keywords
- Maintains database of pushed papers
- Recommends historical papers if no new ones
"""

import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Config
DB_PATH = "/root/.openclaw/workspace/reports/arxiv_papers_db.json"
REPORT_DIR = "/root/.openclaw/workspace/reports"

# Keywords for search (your research interests)
KEYWORDS = [
    "humanoid locomotion reinforcement learning",
    "quadruped robot learning",
    "legged robot reinforcement learning",
    "world model robotics",
    "sim2real legged robots",
    "transformer policy robot",
    "continual learning robotics",
    "teleoperation robot learning",
    "motion imitation humanoid",
    "rapid motor adaptation",
    "teacher student locomotion",
    "whole body control RL",
    "domain randomization locomotion",
    "extreme parkour robot",
]

# Tier-1 Labs (high priority) - 更严格的匹配
TIER1_LABS = [
    "ETH Zurich", "ETH Zürich", "ETHZ", "leggedrobotics",
    "CMU", "Carnegie Mellon",
    "Stanford University", "Stanford AI", "Chelsea Finn", "Xue Bin Peng",
    "MIT ", "MIT's", "Massachusetts Institute", "Improbable AI Lab", "MIT Biomimetics",
    "UC Berkeley", "Berkeley AI", "BAIR",
    "Google Research", "Google DeepMind", "DeepMind",
    "NVIDIA", "NVIDIA Research", "Isaac Lab",
    "Unitree",
    "Agility Robotics",
    "Boston Dynamics",
    "Boston University",
]

# Robotics-related categories
ROBOTICS_CATEGORIES = [
    'cs.RO',  # Robotics
    'cs.LG',  # Machine Learning
    'cs.AI',  # Artificial Intelligence
    'cs.SY',  # Systems and Control
    'eess.SY',  # Systems and Control (EE)
]
TIER2_LABS = [
    "FAIR", "Meta AI",
    "OpenAI",
    "University of Washington",
    "Georgia Tech",
    "Caltech",
    "Harvard",
    "Princeton",
    "Oxford",
    "Cambridge",
    "INRIA",
    "MPI",
    "Tsinghua", "Peking", "Shanghai AI Lab",
]


def load_db():
    """Load papers database"""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return {"papers": [], "last_fetch": None}


def save_db(db):
    """Save papers database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)


def search_arxiv(keyword, max_results=10):
    """Search arXiv for papers"""
    query = urllib.parse.quote(keyword)
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            return parse_arxiv_response(data)
    except Exception as e:
        print(f"Error searching arXiv for '{keyword}': {e}")
        return []


def parse_arxiv_response(xml_data):
    """Parse arXiv XML response"""
    root = ET.fromstring(xml_data)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    papers = []
    for entry in root.findall('atom:entry', ns):
        paper = {}
        paper['id'] = entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else ''
        paper['title'] = entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else ''
        paper['summary'] = entry.find('atom:summary', ns).text.strip()[:300] if entry.find('atom:summary', ns) is not None else ''
        paper['published'] = entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else ''
        paper['updated'] = entry.find('atom:updated', ns).text[:10] if entry.find('atom:updated', ns) is not None else ''
        paper['link'] = entry.find('atom:link[@rel="alternate"]', ns).get('href') if entry.find('atom:link[@rel="alternate"]', ns) is not None else ''
        
        # Authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns)
            if name is not None:
                authors.append(name.text)
        paper['authors'] = authors
        paper['author_str'] = ', '.join(authors[:3])
        if len(authors) > 3:
            paper['author_str'] += ' et al.'
        
        # Categories
        cats = []
        for cat in entry.findall('atom:category', ns):
            cats.append(cat.get('term', ''))
        paper['categories'] = cats
        
        # Generate unique ID
        paper['uid'] = hashlib.md5(paper['id'].encode()).hexdigest()[:12]
        
        papers.append(paper)
    
    return papers


def has_robotics_category(paper):
    """Check if paper has robotics-related categories"""
    cats = paper.get('categories', [])
    return any(cat in ROBOTICS_CATEGORIES for cat in cats)


def is_from_tier1_lab(paper):
    """Check if paper is from tier-1 lab - strict matching"""
    # Combine text fields
    text = ' '.join(paper.get('authors', []))
    text += ' ' + paper.get('summary', '')
    text += ' ' + paper.get('title', '')
    text_lower = text.lower()
    
    # Word boundaries for strict matching
    for lab in TIER1_LABS:
        lab_lower = lab.lower()
        # Check for whole word/phrase match
        if lab_lower in text_lower:
            # Extra validation for short patterns like "MIT"
            if len(lab) <= 4:
                # For short acronyms, check word boundaries
                import re
                pattern = r'\b' + re.escape(lab_lower) + r'\b'
                if re.search(pattern, text_lower):
                    return True
            else:
                return True
    return False


def is_from_tier2_lab(paper):
    """Check if paper is from tier-2 lab - strict matching"""
    text = ' '.join(paper.get('authors', []))
    text += ' ' + paper.get('summary', '')
    text += ' ' + paper.get('title', '')
    text_lower = text.lower()
    
    import re
    for lab in TIER2_LABS:
        lab_lower = lab.lower()
        if lab_lower in text_lower:
            # Use word boundaries for matching
            pattern = r'\b' + re.escape(lab_lower) + r'\b'
            if re.search(pattern, text_lower):
                return True
    return False


def score_paper(paper, today_str):
    """
    Score paper for recommendation priority:
    - New papers from today: high score
    - Tier-1 labs: +50 points
    - Tier-2 labs: +20 points
    """
    score = 0
    
    # Is it new (from today or yesterday)?
    pub_date = paper.get('published', '')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if pub_date == today_str or pub_date == yesterday:
        score += 100  # New paper bonus
    
    # Lab bonus
    if is_from_tier1_lab(paper):
        score += 50
    elif is_from_tier2_lab(paper):
        score += 20
    
    return score


def fetch_and_update():
    """Main function to fetch papers and update database"""
    db = load_db()
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Collect all papers
    all_new_papers = []
    existing_ids = {p['uid'] for p in db.get('papers', [])}
    
    print(f"Searching arXiv for {len(KEYWORDS)} keywords...")
    
    for keyword in KEYWORDS:
        papers = search_arxiv(keyword, max_results=5)
        for paper in papers:
            if paper['uid'] not in existing_ids:
                all_new_papers.append(paper)
                existing_ids.add(paper['uid'])
        print(f"  - '{keyword}': {len(papers)} papers")
    
    # Score and sort new papers, filter for robotics categories
    robotics_papers = []
    for paper in all_new_papers:
        if has_robotics_category(paper):
            paper['score'] = score_paper(paper, today_str)
            paper['discovered_date'] = today_str
            paper['pushed'] = False
            robotics_papers.append(paper)
    
    # Add to database
    db['papers'].extend(robotics_papers)
    db['last_fetch'] = today_str
    
    save_db(db)
    
    print(f"\nTotal new papers found: {len(all_new_papers)}")
    print(f"Robotics-related papers: {len(robotics_papers)}")
    print(f"Database size: {len(db['papers'])} papers")
    
    return robotics_papers, db


def get_papers_to_push(db, max_papers=5):
    """Get papers to push today"""
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # First, try to find new robotics papers that haven't been pushed
    new_candidates = []
    for paper in db.get('papers', []):
        pub_date = paper.get('published', '')
        is_new = (pub_date == today_str or pub_date == yesterday_str)
        if is_new and not paper.get('pushed', False) and has_robotics_category(paper):
            new_candidates.append(paper)
    
    # Sort by score
    new_candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    if new_candidates:
        to_push = new_candidates[:max_papers]
        for p in to_push:
            p['pushed'] = True
            p['push_date'] = today_str
        return to_push, True  # True = new papers
    
    # No new papers, recommend historical ones
    print("No new papers today, recommending historical papers...")
    
    # Get unpushed historical papers with robotics categories, prioritize tier-1 labs
    historical = [p for p in db.get('papers', []) if not p.get('pushed', False) and has_robotics_category(p)]
    
    if not historical:
        # All papers pushed, reset some old ones
        print("Resetting old papers for re-recommendation...")
        for p in db['papers']:
            if p.get('push_date', '') < (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'):
                p['pushed'] = False
        historical = [p for p in db['papers'] if not p.get('pushed', False)]
    
    # Score and sort (boost tier-1 labs)
    for p in historical:
        p['_temp_score'] = score_paper(p, today_str)
        # Extra bonus for tier-1 in historical recommendations
        if is_from_tier1_lab(p):
            p['_temp_score'] += 30
    
    historical.sort(key=lambda x: x.get('_temp_score', 0), reverse=True)
    
    to_push = historical[:max_papers]
    for p in to_push:
        p['pushed'] = True
        p['push_date'] = today_str
    
    return to_push, False  # False = historical papers


def format_paper_markdown(paper, is_new=True):
    """Format paper for markdown report"""
    badge = "🆕" if is_new else "📌"
    lab_indicator = ""
    if is_from_tier1_lab(paper):
        lab_indicator = " ⭐Tier-1 Lab"
    elif is_from_tier2_lab(paper):
        lab_indicator = " 🔸Tier-2 Lab"
    
    md = f"""
### {badge} [{paper['title']}]({paper['link']})

**Authors:** {paper['author_str']}{lab_indicator}

**Published:** {paper['published']} | **Categories:** {', '.join(paper['categories'][:2])}

> {paper['summary']}...

---
"""
    return md


def generate_papers_section():
    """Generate markdown section for daily report"""
    # Fetch new papers
    new_papers, db = fetch_and_update()
    
    # Get papers to push
    papers_to_push, is_new = get_papers_to_push(db, max_papers=5)
    
    # Save updated db
    save_db(db)
    
    # Generate markdown
    md_lines = []
    
    if is_new:
        md_lines.append("## 📄 ArXiv 最新论文")
        md_lines.append("")
        md_lines.append(f"_今日发现 {len(new_papers)} 篇新论文，推送 Top {len(papers_to_push)}_")
        md_lines.append("")
    else:
        md_lines.append("## 📄 ArXiv 论文推荐 (今日无新论文)")
        md_lines.append("")
        md_lines.append("_从历史论文中精选，优先展示高影响力实验室工作_")
        md_lines.append("")
    
    for paper in papers_to_push:
        md_lines.append(format_paper_markdown(paper, is_new))
    
    md_lines.append("")
    md_lines.append(f"_论文数据库: {len(db['papers'])} 篇 | 本次{'新论文' if is_new else '历史推荐'}_")
    
    return '\n'.join(md_lines), is_new, len(papers_to_push)


if __name__ == "__main__":
    section, is_new, count = generate_papers_section()
    
    # Save section for report script to include
    os.makedirs(REPORT_DIR, exist_ok=True)
    section_file = os.path.join(REPORT_DIR, "arxiv_section.md")
    with open(section_file, 'w') as f:
        f.write(section)
    
    print(f"\n{'='*50}")
    print(f"ArXiv section generated: {section_file}")
    print(f"Type: {'New papers' if is_new else 'Historical recommendation'}")
    print(f"Count: {count} papers")
    print(f"{'='*50}")
    
    # Print the section
    print(section)
