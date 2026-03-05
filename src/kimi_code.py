#!/usr/bin/env python3
"""
Kimi Code - CLI tool for Kimi API integration using OpenAI SDK
Logs all operations to file instead of stdout
"""

import os
import sys
import json
import logging
import argparse
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

# Import OpenAI SDK
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.error("OpenAI SDK not available")

# API Configuration
KIMI_API_KEY = os.environ.get('KIMI_API_KEY') or "sk-kimi-csx7jTKeTi48D4rfP1nldksBx9snydd7foY6ffPp7nRSkbmSSAmwARvAXJ5rOJyb"
KIMI_BASE_URL = os.environ.get('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
KIMI_MODEL = os.environ.get('KIMI_MODEL', 'kimi-k2-5')


def get_client():
    """Get OpenAI client configured for Kimi"""
    if not OPENAI_AVAILABLE:
        return None
    return OpenAI(
        api_key=KIMI_API_KEY,
        base_url=KIMI_BASE_URL
    )


def call_kimi_api(prompt, model=None, temperature=0.3, max_tokens=4096):
    """Call Kimi API using OpenAI SDK"""
    client = get_client()
    if not client:
        return "Error: OpenAI SDK not available"
    
    model = model or KIMI_MODEL
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant. Provide concise, practical code solutions."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"API call successful. Usage: {response.usage}")
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f'API Error: {str(e)}')
        return f'Error: {str(e)}'


def analyze_paper(paper_title, paper_abstract, authors=None):
    """Analyze a research paper using Kimi"""
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
    response = call_kimi_api(prompt, temperature=0.2)
    logger.info(f'Analysis completed for: {paper_title[:60]}...')
    
    return response


def code_review(file_path, code_content):
    """Review code using Kimi"""
    prompt = f"""Review this code and provide feedback:

File: {file_path}

```python
{code_content}
```

Check for:
1. Bugs or logical errors
2. Python best practices (PEP8)
3. Performance issues
4. Missing error handling
5. Documentation needs

Provide specific line-by-line suggestions where applicable.
"""
    
    logger.info(f'Reviewing code: {file_path}')
    response = call_kimi_api(prompt, temperature=0.2)
    logger.info(f'Code review completed for: {file_path}')
    
    return response


def generate_code(task_description, context=None):
    """Generate code using Kimi"""
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
    response = call_kimi_api(prompt, temperature=0.3)
    logger.info('Code generation completed')
    
    return response


def main():
    parser = argparse.ArgumentParser(description='Kimi Code - AI coding assistant')
    parser.add_argument('command', choices=['analyze', 'review', 'generate', 'ask'], 
                       help='Command to run')
    parser.add_argument('--file', '-f', help='File path for review')
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
            logger.error('Missing --title or --abstract for analyze command')
            sys.exit(1)
        result = analyze_paper(args.title, args.abstract, args.authors)
    
    elif args.command == 'review':
        if not args.file:
            logger.error('Missing --file for review command')
            sys.exit(1)
        try:
            with open(args.file, 'r') as f:
                code = f.read()
            result = code_review(args.file, code)
        except Exception as e:
            logger.error(f'Failed to read file: {e}')
            sys.exit(1)
    
    elif args.command == 'generate':
        if not args.task:
            logger.error('Missing --task for generate command')
            sys.exit(1)
        result = generate_code(args.task)
    
    elif args.command == 'ask':
        if not args.prompt:
            logger.error('Missing --prompt for ask command')
            sys.exit(1)
        result = call_kimi_api(args.prompt)
    
    else:
        logger.error(f'Unknown command: {args.command}')
        sys.exit(1)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        logger.info(f'Result written to: {args.output}')
    else:
        # Write to a temp result file for later retrieval
        result_file = os.path.join(LOG_DIR, 'last_result.txt')
        with open(result_file, 'w') as f:
            f.write(result)
        logger.info(f'Result saved to: {result_file}')


if __name__ == '__main__':
    main()
