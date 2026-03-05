#!/bin/bash
# Daily RL Infra Report Generator - 运控RL领域日报
# Optimized for: 人形/四足机器人运控、RL Infra、Sim2Real、World Model
# Runs at 09:00 Asia/Shanghai

REPORT_DIR="/root/.openclaw/workspace/reports"
mkdir -p "$REPORT_DIR"

DATE=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
REPORT_FILE="$REPORT_DIR/rl_report_${DATE}.md"

echo "# 📊 运控RL每日报告 - ${DATE}" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_针对 Ezio's RL ToolBox 开发者的个性化日报_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ============================================
# 1. ArXiv 论文推送 + 智能分析
# ============================================
echo "## 📄 正在获取 ArXiv 论文..." >&2
python3 /root/.openclaw/workspace/scripts/arxiv_tracker.py > /dev/null 2>&1

# 运行论文分析器
echo "## 🧠 正在分析论文相关性..." >&2
python3 /root/.openclaw/workspace/scripts/paper_analyzer.py > /dev/null 2>&1

# 运行LLM深度分析（预算控制：只分析前3篇）
echo "## 🔬 正在运行LLM深度分析..." >&2
python3 /root/.openclaw/workspace/scripts/llm_analyzer.py > /dev/null 2>&1

# 生成预算报告
echo "## 💰 正在生成预算报告..." >&2
python3 /root/.openclaw/workspace/scripts/budget_tracker.py > /dev/null 2>&1

# 添加论文分析到报告
if [ -f "$REPORT_DIR/paper_analysis.md" ]; then
  cat "$REPORT_DIR/paper_analysis.md" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
fi

# 添加预算报告
if [ -f "$REPORT_DIR/budget_report.md" ]; then
  cat "$REPORT_DIR/budget_report.md" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
fi

# ============================================
# 2. 你的 Toolbox 昨日更改
# ============================================
echo "## 🔧 Ezio-s_RL_Toolbox 昨日动态" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

COMMITS=$(gh api repos/eziothean-git/Ezio-s_RL_Toolbox/commits --paginate --jq "
  [.[] | select(.commit.committer.date | startswith(\"${YESTERDAY}\")) | \
  {msg: .commit.message, author: .commit.author.name, url: .html_url, sha: .sha[:7]}]
")

if [ "$COMMITS" != "[]" ] && [ -n "$COMMITS" ]; then
  echo "### 昨日提交 (${YESTERDAY})" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "$COMMITS" | jq -r '.[] | "- **\(.sha)** \(.msg) — *\(.author)*"' >> "$REPORT_FILE"
else
  echo "_昨日无新提交_" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 获取最近的 PRs
PRS=$(gh pr list --repo eziothean-git/Ezio-s_RL_Toolbox --state all --limit 5 --json title,number,state,updatedAt,url 2>/dev/null)
if [ "$PRS" != "[]" ] && [ -n "$PRS" ]; then
  echo "### 最近 PRs" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "$PRS" | jq -r '.[] | "- [#\(.number)] \(.title) (\(.state)) — [查看](\(.url))"' >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
fi

# ============================================
# 3. 核心框架监控 (与你ToolBox直接相关)
# ============================================
echo "## 🏗️ 核心框架动态" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Isaac Lab / rsl_rl / MuJoCo 等基础设施更新_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

CORE_REPOS=(
  "isaac-sim/IsaacLab:Isaac Lab (核心训练后端)"
  "isaac-sim/IsaacGymEnvs:IsaacGym (旧版训练后端)"
  "leggedrobotics/rsl_rl:rsl_rl (算法层)"
  "google-deepmind/mujoco:MuJoCo (sim2sim/部署)"
  "leggedrobotics/legged_gym:legged_gym (ETH参考实现)"
)

for item in "${CORE_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  LATEST=$(gh api repos/${repo}/commits --jq '.[0] | {msg: .commit.message[:60], date: .commit.committer.date[:10], sha: .sha[:7], author: .commit.author.name}' 2>/dev/null)
  if [ -n "$LATEST" ] && [ "$LATEST" != "null" ]; then
    MSG=$(echo "$LATEST" | jq -r '.msg')
    DATE=$(echo "$LATEST" | jq -r '.date')
    SHA=$(echo "$LATEST" | jq -r '.sha')
    AUTHOR=$(echo "$LATEST" | jq -r '.author')
    echo "- **${label}** — \`${SHA}\` ${MSG}... (${DATE}, ${AUTHOR})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 4. 人形机器人运控前沿
# ============================================
echo "## 🤖 人形机器人运控" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Humanoid Locomotion / Teleoperation / Whole-body Control_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

HUMANOID_REPOS=(
  "cmu-humanoids/vision-guided-walking:CMU Vision-Guided Walking"
  "cassie-cal/cassie-mujoco-sim:Cassie仿真"
  "unitreerobotics/unitree_ros2:Unitree ROS2"
  "google-research/humanoid-gym:Google Humanoid Gym"
  "carlmanager/humanoid-rl:Humanoid RL训练"
  "Takahashi-Ke/Pink:MIT Pink Controller"
)

for item in "${HUMANOID_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{msg: .commit.message[:50], date: .pushed_at[:10], stars: .stargazers_count, desc: (.description // "")[:40]}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    DESC=$(echo "$INFO" | jq -r '.desc')
    echo "- **${label}** ⭐${STARS} — ${DESC}... (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 5. 四足机器人运控
# ============================================
echo "## 🐕 四足机器人运控" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Quadruped Locomotion / Extreme Parkour / RMA / PMTG_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

QUAD_REPOS=(
  "agilityrobotics/isaac-quadruped:Agility Robotics"
  "mit-biomimetics/Cheetah-Software:MIT Cheetah"
  "ethz-adrl/control-toolbox:ETH Control Toolbox"
  "jviereck/eth_mpc_pybullet:ETH MPC PyBullet"
  "google-research/motion_imitation:Google Motion Imitation"
)

for item in "${QUAD_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{date: .pushed_at[:10], stars: .stargazers_count, desc: (.description // "")[:40]}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    DESC=$(echo "$INFO" | jq -r '.desc')
    echo "- **${label}** ⭐${STARS} — ${DESC}... (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 6. Sim2Real & 世界模型
# ============================================
echo "## 🔄 Sim2Real & World Model" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Domain Randomization / System Identification / World Model for Robotics_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

SIM2REAL_REPOS=(
  "xukuanHIT/Phygital:物理驱动的世界模型"
  "nvidia-isaac/IsaacGymEnvs:NVIDIA Isaac"
  "ethz-asl/robot_learning_ws:ETH RL Workshop"
  "arise-impact/robust-robotics:Robust Robotics"
)

for item in "${SIM2REAL_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{date: .pushed_at[:10], stars: .stargazers_count}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    echo "- **${label}** ⭐${STARS} (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 7. Transformer for Robotics / Continual Learning
# ============================================
echo "## 🧠 Transformer策略 & 持续学习" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Transformer-based Policy / Attention / Continual Learning for Locomotion_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

ADVANCED_REPOS=(
  "facebookresearch/habitat-lab:Habitat Lab (Sim2Real)"
  "google-research/robustness_metrics:Robustness Metrics"
  "facebookresearch/fairo:FAIR Robotics"
  "nvidia-project-mosaic/mosaic:Multi-Task Learning"
)

for item in "${ADVANCED_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{date: .pushed_at[:10], stars: .stargazers_count}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    echo "- **${label}** ⭐${STARS} (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 8. RL Infra & 工具链
# ============================================
echo "## 🛠️ RL Infra & 工具链" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_与你Ezio's ToolBox类似的框架/工具_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

INFRA_REPOS=(
  "skylark-interactive/simulator-agnostic-rl:Simulator Agnostic RL"
  "epignatelli/lambs:LAMBS (Learning Abstract Machines)"
  "thu-ml/tianshou:Tianshou RL框架"
  "facebookresearch/theseus:Theseus (可微分优化)"
  "pytorch/rl:PyTorch RL"
  "google/brax:Brax (JAX RL)"
)

for item in "${INFRA_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{date: .pushed_at[:10], stars: .stargazers_count, desc: (.description // "")[:50]}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    DESC=$(echo "$INFO" | jq -r '.desc')
    echo "- **${label}** ⭐${STARS} — ${DESC}... (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# 9. 遥操作 & MoCap替代
# ============================================
echo "## 🎮 遥操作 & MoCap替代方案" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "_Teleoperation / Learning from Observation / Motion Generation_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TELEOP_REPOS=(
  "tonyzhaozh/robomimic:Robomimic (模仿学习)"
  "arvrse/robomimic:Robomimic Fork"
  "joonspk-research/generativeagents:Generative Agents"
  "huggingface/lerobot:LeRobot (Hugging Face)"
)

for item in "${TELEOP_REPOS[@]}"; do
  IFS=':' read -r repo label <<< "$item"
  INFO=$(gh api repos/${repo} --jq '{date: .pushed_at[:10], stars: .stargazers_count}' 2>/dev/null)
  if [ -n "$INFO" ] && [ "$INFO" != "null" ]; then
    DATE=$(echo "$INFO" | jq -r '.date')
    STARS=$(echo "$INFO" | jq -r '.stars')
    echo "- **${label}** ⭐${STARS} (${DATE})" >> "$REPORT_FILE"
  fi
done
echo "" >> "$REPORT_FILE"

# ============================================
# Footer
# ============================================
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "📅 _报告生成时间: $(date '+%Y-%m-%d %H:%M:%S %Z')_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "💡 _ArXiv论文追踪数据库: ${REPORT_DIR}/arxiv_papers_db.json_" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "🤖 _Enjoy your daily dose of RL locomotion research!_" >> "$REPORT_FILE"

# 输出报告路径
echo "$REPORT_FILE"
