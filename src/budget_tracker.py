#!/usr/bin/env python3
"""
Budget Tracker for Kimi API
监控API使用情况和预算消耗
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

LOGS_DIR = "/root/.openclaw/workspace/logs"
REPORTS_DIR = "/root/.openclaw/workspace/reports"
BUDGET_FILE = os.path.join(REPORTS_DIR, "budget_tracking.json")

# 定价配置 (Kimi K2.5)
PRICING = {
    "kimi-k2.5": {
        "input_cache_hit": 0.70,    # 元/百万tokens
        "input_cache_miss": 4.00,   # 元/百万tokens
        "output": 21.00             # 元/百万tokens
    }
}

# 预算配置
BUDGET_CONFIG = {
    "monthly_limit": 50.0,  # 假设40% Allegretto Plan = 50元/月
    "daily_limit": 5.0,     # 每日上限
    "per_paper_limit": 0.5  # 单篇论文分析上限
}


def load_budget_data():
    """加载预算数据"""
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, 'r') as f:
            return json.load(f)
    return {
        "monthly_usage": {},
        "daily_usage": {},
        "total_tokens": {"input": 0, "output": 0},
        "total_cost": 0.0
    }


def save_budget_data(data):
    """保存预算数据"""
    os.makedirs(os.path.dirname(BUDGET_FILE), exist_ok=True)
    with open(BUDGET_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def estimate_paper_analysis_cost():
    """估算单篇论文分析成本"""
    # 输入: 论文标题 + 摘要 + 提示词 ≈ 3000 tokens
    # 输出: 分析结果 ≈ 1500 tokens
    input_tokens = 3000
    output_tokens = 1500
    
    # 假设缓存未命中（首次调用）
    input_cost = (input_tokens / 1_000_000) * PRICING["kimi-k2.5"]["input_cache_miss"]
    output_cost = (output_tokens / 1_000_000) * PRICING["kimi-k2.5"]["output"]
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }


def check_budget_status():
    """检查预算状态"""
    data = load_budget_data()
    today = datetime.now().strftime('%Y-%m-%d')
    month_key = datetime.now().strftime('%Y-%m')
    
    # 今日使用
    daily_usage = data.get("daily_usage", {}).get(today, 0)
    
    # 本月使用
    monthly_usage = data.get("monthly_usage", {}).get(month_key, 0)
    
    # 估算剩余可用
    daily_remaining = BUDGET_CONFIG["daily_limit"] - daily_usage
    monthly_remaining = BUDGET_CONFIG["monthly_limit"] - monthly_usage
    
    # 单篇成本
    per_paper = estimate_paper_analysis_cost()
    
    return {
        "today_usage": daily_usage,
        "today_remaining": daily_remaining,
        "today_limit": BUDGET_CONFIG["daily_limit"],
        "month_usage": monthly_usage,
        "month_remaining": monthly_remaining,
        "month_limit": BUDGET_CONFIG["monthly_limit"],
        "per_paper_cost": per_paper["total_cost"],
        "papers_available_today": int(daily_remaining / per_paper["total_cost"]),
        "papers_available_month": int(monthly_remaining / per_paper["total_cost"])
    }


def record_usage(input_tokens, output_tokens, description=""):
    """记录API使用"""
    data = load_budget_data()
    today = datetime.now().strftime('%Y-%m-%d')
    month_key = datetime.now().strftime('%Y-%m')
    
    # 计算成本
    input_cost = (input_tokens / 1_000_000) * PRICING["kimi-k2.5"]["input_cache_miss"]
    output_cost = (output_tokens / 1_000_000) * PRICING["kimi-k2.5"]["output"]
    total_cost = input_cost + output_cost
    
    # 更新统计
    data["total_tokens"]["input"] += input_tokens
    data["total_tokens"]["output"] += output_tokens
    data["total_cost"] += total_cost
    
    # 更新日使用
    if today not in data["daily_usage"]:
        data["daily_usage"][today] = 0
    data["daily_usage"][today] += total_cost
    
    # 更新月使用
    if month_key not in data["monthly_usage"]:
        data["monthly_usage"][month_key] = 0
    data["monthly_usage"][month_key] += total_cost
    
    # 记录明细
    if "history" not in data:
        data["history"] = []
    data["history"].append({
        "timestamp": datetime.now().isoformat(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": total_cost,
        "description": description
    })
    
    save_budget_data(data)
    return total_cost


def generate_budget_report():
    """生成预算报告"""
    status = check_budget_status()
    data = load_budget_data()
    
    lines = []
    lines.append("## 💰 API预算监控")
    lines.append("")
    
    # 今日状态
    lines.append("### 今日使用")
    lines.append(f"- 已用: ¥{status['today_usage']:.4f} / ¥{status['today_limit']}")
    lines.append(f"- 剩余: ¥{status['today_remaining']:.4f}")
    lines.append(f"- 可分析论文: {status['papers_available_today']} 篇")
    lines.append("")
    
    # 本月状态
    lines.append("### 本月使用")
    lines.append(f"- 已用: ¥{status['month_usage']:.4f} / ¥{status['month_limit']}")
    lines.append(f"- 剩余: ¥{status['month_remaining']:.4f}")
    lines.append(f"- 可分析论文: {status['papers_available_month']} 篇")
    lines.append("")
    
    # 成本估算
    lines.append("### 成本估算")
    lines.append(f"- 单篇论文分析: ¥{status['per_paper_cost']:.4f}")
    lines.append(f"  - 输入: ~3K tokens")
    lines.append(f"  - 输出: ~1.5K tokens")
    lines.append("")
    
    # 历史总计
    lines.append("### 历史总计")
    lines.append(f"- 总消耗: ¥{data.get('total_cost', 0):.4f}")
    lines.append(f"- 总输入: {data.get('total_tokens', {}).get('input', 0):,} tokens")
    lines.append(f"- 总输出: {data.get('total_tokens', {}).get('output', 0):,} tokens")
    lines.append("")
    
    # 定价参考
    lines.append("### 定价参考 (Kimi K2.5)")
    lines.append(f"- 输入 (缓存未命中): ¥{PRICING['kimi-k2.5']['input_cache_miss']}/M tokens")
    lines.append(f"- 输入 (缓存命中): ¥{PRICING['kimi-k2.5']['input_cache_hit']}/M tokens")
    lines.append(f"- 输出: ¥{PRICING['kimi-k2.5']['output']}/M tokens")
    
    return '\n'.join(lines)


def main():
    """主函数"""
    report = generate_budget_report()
    print(report)
    
    # 保存报告
    report_path = os.path.join(REPORTS_DIR, "budget_report.md")
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
