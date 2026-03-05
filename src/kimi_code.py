#!/usr/bin/env python3
"""
Kimi Code - CLI tool using OpenClaw's model routing
Uses moonshot/kimi-k2.5 via OpenClaw sessions_spawn
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Setup logging to file
LOG_DIR = os.environ.get('DEV_LOG_DIR', '/root/.openclaw/workspace/logs')
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f'kimi_code_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
    ]
)
logger = logging.getLogger('kimi_code')

# Model configuration - use OpenClaw's moonshot provider
MODEL = "moonshot/kimi-k2.5"


def call_kimi_via_openclaw(prompt, temperature=0.3, max_tokens=4096):
    """Call Kimi via OpenClaw sessions_spawn"""
    
    # Create a temporary task file
    task_content = f"""Please respond to the following prompt. Be concise and helpful.

Prompt: {prompt}

Requirements:
- Temperature: {temperature}
- Max tokens: {max_tokens}
- Provide structured, practical output
"""
    
    logger.info(f"Calling OpenClaw with model {MODEL}")
    
    try:
        # Use openclaw sessions_spawn to call the model
        cmd = [
            'openclaw', 'sessions_spawn',
            '--task', task_content,
            '--model', MODEL,
            '--runTimeoutSeconds', '120',
            '--cleanup', 'delete'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            logger.error(f"OpenClaw error: {result.stderr}")
            return f"Error: {result.stderr}"
        
        # Extract response from output
        response = result.stdout
        logger.info(f"Response received, length: {len(response)}")
        return response
        
    except subprocess.TimeoutExpired:
        logger.error("OpenClaw call timed out")
        return "Error: Request timed out"
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return f"Error: {str(e)}"


def analyze_paper(paper_title, paper_abstract, authors=None):
    """Analyze a research paper using Kimi via OpenClaw"""
    prompt = f"""Analyze this robotics/RL paper and provide a structured summary.

Title: {paper_title}
Authors: {authors or 'N/A'}
Abstract: {paper_abstract}

Provide analysis in this format:

## One-Line Summary
(One sentence capturing the core contribution)

## Core Method
- What problem does it solve?
- Key technical approach
- Main innovation

## Experimental Validation
- Test environments/tasks
- Key results (numbers if available)
- Comparison to baselines

## Relevance to Legged Robot Locomotion
Score 1-10 and explain why

## Actionable Insights
What can be directly applied to RL framework development?

## Code/Resources
Mention if code/data is available or referenced.
"""
    
    logger.info(f'Analyzing paper: {paper_title[:60]}...')
    response = call_kimi_via_openclaw(prompt, temperature=0.2)
    logger.info(f'Analysis completed')
    
    return response


def generate_code(task_description, context=None):
    """Generate code using Kimi via OpenClaw"""
    context_str = f'\nContext: {context}' if context else ''
    
    prompt = f"""Generate Python code for this task:

Task: {task_description}{context_str}

Requirements:
- Clean, readable Python 3.10+
- Include docstrings and type hints
- Add error handling
- Follow PEP8
- Include example usage

Output only the code block.
"""
    
    logger.info(f'Generating code for: {task_description[:60]}...')
    response = call_kimi_via_openclaw(prompt, temperature=0.3)
    logger.info('Code generation completed')
    
    return response


def main():
    parser = argparse.ArgumentParser(description='Kimi Code - AI coding assistant via OpenClaw')
    parser.add_argument('command', choices=['analyze', 'generate', 'ask'], 
                       help='Command to run')
    parser.add_argument('--title', '-t', help='Paper title for analysis')
    parser.add_argument('--abstract', '-a', help='Paper abstract')
    parser.add_argument('--authors', help='Paper authors')
    parser.add_argument('--task', help='Task description for code generation')
    parser.add_argument('--prompt', '-p', help='Direct prompt for ask command')
    parser.add_argument('--output', '-o', help='Output file (optional)')
    
    args = parser.parse_args()
    
    logger.info(f'Command: {args.command}')
    
    if args.command == 'analyze':
        if not args.title or not args.abstract:
            logger.error('Missing --title or --abstract')
            sys.exit(1)
        result = analyze_paper(args.title, args.abstract, args.authors)
    
    elif args.command == 'generate':
        if not args.task:
            logger.error('Missing --task')
            sys.exit(1)
        result = generate_code(args.task)
    
    elif args.command == 'ask':
        if not args.prompt:
            logger.error('Missing --prompt')
            sys.exit(1)
        result = call_kimi_via_openclaw(args.prompt)
    
    else:
        logger.error(f'Unknown command: {args.command}')
        sys.exit(1)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        logger.info(f'Result written to: {args.output}')
    else:
        # Write to a temp result file
        result_file = os.path.join(LOG_DIR, 'last_result.txt')
        with open(result_file, 'w') as f:
            f.write(result)
        logger.info(f'Result saved to: {result_file}')
        print(result)  # Also print to stdout for immediate feedback


if __name__ == '__main__':
    main()
