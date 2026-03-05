#!/usr/bin/env python3
"""
Generate GitHub repositories report
"""
import json
import subprocess
from datetime import datetime

REPOS = {
    "🏗️ 核心训练框架": [
        ("isaac-sim/IsaacLab", "Isaac Lab", "NVIDIA仿真训练框架"),
        ("isaac-sim/IsaacGymEnvs", "IsaacGym", "GPU并行仿真"),
        ("google-deepmind/mujoco", "MuJoCo", "物理仿真引擎"),
        ("gymnasium/gymnasium", "Gymnasium", "RL环境标准"),
    ],
    "🧠 算法与策略": [
        ("leggedrobotics/rsl_rl", "rsl_rl", "ETH RL算法库"),
        ("openai/baselines", "OpenAI Baselines", "经典RL算法"),
        ("DLR-RM/stable-baselines3", "SB3", "稳定RL算法"),
        ("thu-ml/tianshou", "Tianshou", "国产RL框架"),
        ("google/brax", "Brax", "JAX并行RL"),
    ],
    "🤖 人形机器人": [
        ("cmu-humanoids/vision-guided-walking", "CMU Vision Walking", "视觉引导行走"),
        ("unitreerobotics/unitree_ros2", "Unitree ROS2", "宇树ROS2接口"),
    ],
    "🐕 四足机器人": [
        ("mit-biomimetics/Cheetah-Software", "MIT Cheetah", "猎豹软件"),
        ("ethz-adrl/control-toolbox", "ETH Control", "ETH控制工具箱"),
        ("google-research/motion_imitation", "Motion Imitation", "动作模仿"),
    ],
    "🔄 Sim2Real": [
        ("facebookresearch/habitat-lab", "Habitat", "Sim2Real平台"),
    ],
    "🎮 遥操作与模仿": [
        ("tonyzhaozh/robomimic", "Robomimic", "模仿学习"),
        ("huggingface/lerobot", "LeRobot", "HuggingFace机器人"),
    ],
    "🛠️ 工具与基础设施": [
        ("facebookresearch/theseus", "Theseus", "可微分优化"),
        ("pytorch/rl", "PyTorch RL", "PyTorch RL库"),
    ],
}

def get_repo_info(repo):
    """获取仓库信息"""
    try:
        info = subprocess.run(
            ['gh', 'api', f'repos/{repo}'],
            capture_output=True, text=True, timeout=10
        )
        if info.returncode != 0:
            return None
        
        data = json.loads(info.stdout)
        
        commits = subprocess.run(
            ['gh', 'api', f'repos/{repo}/commits', '-q', '.[0]'],
            capture_output=True, text=True, timeout=10
        )
        latest_commit = None
        if commits.returncode == 0:
            latest_commit = json.loads(commits.stdout)
        
        return {
            'stars': data.get('stargazers_count', 0),
            'updated': data.get('pushed_at', '')[:10],
            'desc': data.get('description', 'No description')[:50],
            'commit': latest_commit,
            'url': data.get('html_url', '')
        }
    except:
        return None

def main():
    print("## 🚀 GitHub 项目动态雷达\n")
    print("_监控25+个相关开源项目最新动态_\n")
    
    total_repos = 0
    active_repos = 0
    
    for category, repos in REPOS.items():
        print(f"### {category}")
        print("")
        
        for repo, name, desc in repos:
            info = get_repo_info(repo)
            if info:
                total_repos += 1
                
                commit_info = ""
                if info['commit']:
                    commit_data = info['commit'].get('commit', {})
                    msg = commit_data.get('message', '')[:40]
                    date = info['commit'].get('commit', {}).get('committer', {}).get('date', '')[:10]
                    sha = info['commit'].get('sha', '')[:7]
                    
                    # 检查是否是最近7天的提交
                    try:
                        from datetime import datetime
                        commit_date = datetime.fromisoformat(info['commit'].get('commit', {}).get('committer', {}).get('date', '').replace('Z', '+00:00'))
                        days_ago = (datetime.now() - commit_date).days
                        if days_ago <= 7:
                            active_repos += 1
                            commit_info = f" | 🟢 {days_ago}天前: {msg}..."
                        else:
                            commit_info = f" | {date}: {msg}..."
                    except:
                        commit_info = f" | {date}: {msg}..."
                
                print(f"- **[{name}]({info['url']})** ⭐{info['stars']:,} - {info['desc']}{commit_info}")
            else:
                print(f"- **{name}** - {desc}")
        
        print("")
    
    print(f"📊 **监控统计**: 共 {total_repos} 个项目，其中 **{active_repos}** 个最近7天有更新\n")

if __name__ == "__main__":
    main()
