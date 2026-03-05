#!/bin/bash
# Daily RL Report Generator - Enhanced Version
# Focus: Neural Network + Deep RL for Robotics

REPORT_DIR="/root/.openclaw/workspace/reports"
PDF_DIR="$REPORT_DIR/pdfs"
mkdir -p "$REPORT_DIR" "$PDF_DIR"

DATE=$(date +%Y-%m-%d)
REPORT_FILE="$REPORT_DIR/rl_report_${DATE}.md"

echo "正在生成增强版日报..." >&2

# 创建报告头部
cat > "$REPORT_FILE" << EOF
# 📊 运控RL每日报告

> 🤖 **基于神经网络的强化学习日报**  
> 📅 报告日期：${DATE}  
> 🎯 针对 Ezio's RL ToolBox 开发者

---

EOF

# ============================================
# 1. 获取ArXiv论文
# ============================================
echo "📄 正在获取ArXiv论文..." >&2
python3 /root/.openclaw/workspace/scripts/arxiv_tracker.py > /dev/null 2>&1

# ============================================
# 2. 生成论文详细报告
# ============================================
echo "🧠 正在生成论文详细报告..." >&2
echo "" >> "$REPORT_FILE"
python3 /root/.openclaw/workspace/scripts/generate_paper_report.py >> "$REPORT_FILE" 2>&1

# ============================================
# 3. GitHub项目动态
# ============================================
echo "🚀 正在获取GitHub项目动态..." >&2
echo "" >> "$REPORT_FILE"
python3 /root/.openclaw/workspace/scripts/generate_github_report.py >> "$REPORT_FILE" 2>&1

# ============================================
# 4. Toolbox昨日动态
# ============================================
echo "" >> "$REPORT_FILE"
echo "## 🔧 Ezio-s_RL_Toolbox 昨日动态" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_监控你的代码仓库变更_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

COMMITS=$(gh api repos/eziothean-git/Ezio-s_RL_Toolbox/commits --paginate --jq "
  [.[] | select(.commit.committer.date | startswith(\"${YESTERDAY}\")) | \
  {msg: .commit.message, author: .commit.author.name, url: .html_url, sha: .sha[:7]}]
" 2>/dev/null)

if [ "$COMMITS" != "[]" ] && [ -n "$COMMITS" ]; then
  echo "### 💻 昨日提交 (${YESTERDAY})" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "$COMMITS" | jq -r '.[] | "- **\(.sha)** \(.msg | split(\"\\n\")[0]) — *\(.author)*"' >> "$REPORT_FILE"
else
  echo "_昨日无新提交_" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# ============================================
# 5. 今日待办
# ============================================
cat >> "$REPORT_FILE" << EOF

## ✅ 今日待办

基于你的研究方向，建议今天关注：

1. [ ] 📖 阅读 Top 5 论文的PDF版本（已下载到 \`${PDF_DIR}/\`）
2. [ ] 🔍 检查 rsl_rl 更新对你的代码影响
3. [ ] 💡 评估新方法是否可集成到 ToolBox

EOF

# ============================================
# 6. 资源导航
# ============================================
cat >> "$REPORT_FILE" << EOF

## 📁 本地资源导航

| 资源类型 | 位置 |
|---------|------|
| 📄 完整报告 | \`${REPORT_FILE}\` |
| 📚 PDF论文 | \`${PDF_DIR}/\` |
| 📊 论文数据库 | \`${REPORT_DIR}/arxiv_papers_db.json\` |

---

<div align="center">

📅 报告生成时间: $(date '+%Y-%m-%d %H:%M:%S %Z')  
🤖 由 Kimi Claw 自动生成  
📮 下次推送: 明天 09:00 (Asia/Shanghai)

</div>
EOF

echo "✅ 报告生成完成: $REPORT_FILE" >&2
echo "$REPORT_FILE"
