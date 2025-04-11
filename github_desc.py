import os
import argparse
import pyperclip
import requests
from github import Github
from openai import OpenAI as DeepseekClient
from rich.console import Console
from rich.markdown import Markdown

# Check required environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not GITHUB_TOKEN:
    raise Exception("🚫 GITHUB_TOKEN environment variable not set")
if not DEEPSEEK_API_KEY:
    raise Exception("🚫 DEEPSEEK_API_KEY environment variable not set")

def get_pr_diff(pr_url):
    """
    Fetches the diff (patch) for a pull request from a private repository.
    Expected PR URL format: https://github.com/{owner}/{repo}/pull/{pr_number}
    """
    print("🔍 Fetching PR diff from GitHub...")
    
    g = Github(GITHUB_TOKEN)
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 7:
        raise Exception("🚫 Invalid PR URL format")
    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])
    
    repository = g.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    
    api_url = pr.url
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"🚫 Error fetching diff: {response.status_code} {response.text}")
    
    print("✅ PR diff fetched successfully!")
    return response.text

def analyze_diff_with_deepseek(diff_text):
    """
    Analyzes the diff with Deepseek.
    """
    print("🤖 Analyzing diff with Deepseek...")
    
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a code analysis assistant."},
            {"role": "user", "content": diff_text}
        ],
        stream=False
    )
    
    print("✅ Diff analysis completed!")
    return response.choices[0].message.content

def generate_formatted_pr_report(diff_text, analysis_text, target, pr_link):
    """
    Generates a formatted PR report.
    
    For GitHub (default), the output uses markdown headers.
    
    For Slack, the output uses simple Slack mrkdwn formatting. The template is:
    
    Guys, please review the following PR.
    
    *PR Link:* <{pr_link}>
    
    *Description:*  
    {description}
    
    *Why:*  
    {why}
    
    *Risks:*  
    {risks}
    
    *Code Snippets & Explanation:*  
    {code_snippet_explanation}
    
    Any code snippets in the "Code Snippets & Explanation" section should be wrapped in triple backticks (```).
    """
    print("📝 Generating formatted PR report with Deepseek...")
    
    if target.lower() == "slack":
        prompt_template = """
You are an assistant that summarizes code changes for a pull request.
Based on the provided diff and analysis, generate a Slack formatted report exactly as follows.
Please ensure to wrap any code snippets in triple backticks (```) so that Slack renders them as code blocks.

Guys, please review the following PR.

*PR Link:* <{pr_link}>

*Description:*  
{description}

*Why:*  
{why}

*Risks:*  
{risks}

*Code Snippets & Explanation:*  
{code_snippet_explanation}

Fill in each section appropriately. Output only the content in the template.
""".strip()
    else:  # Default GitHub formatting using markdown
        prompt_template = """
You are an assistant that summarizes code changes for a pull request.
Based on the provided diff and analysis, generate a markdown formatted report following this template exactly:

## Description 📝
{description}

## Why? ✅
{why}

## Risks? ⚠️
{risks}

## Code Snippets & Explanation 📑
{code_snippet_explanation}

Fill in each section appropriately. Output only the content in the template.
""".strip()
    
    filled_prompt = prompt_template.format(
        description="[Summarize the changes and key updates.]",
        why="[Explain the reasoning and motivation behind the changes.]",
        risks="[List any potential risks or side effects.]",
        code_snippet_explanation="[Extract and explain relevant code snippet(s) from the diff; if including code, wrap it in triple backticks (```).]",
        pr_link=pr_link
    )
    
    final_prompt = f"{filled_prompt}\n\nHere is the diff:\n{diff_text}\n\nAnalysis:\n{analysis_text}"
    
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates a detailed PR report."},
            {"role": "user", "content": final_prompt}
        ],
        stream=False
    )
    
    print("✅ Formatted PR report generated!")
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted PR report using Deepseek and GitHub API"
    )
    parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    parser.add_argument("--target", choices=["github", "slack"], default="github",
                        help="Output format target (default: github)")
    args = parser.parse_args()
    
    console = Console()
    try:
        print("🚀 Starting PR report generation process...\n")
        diff_text = get_pr_diff(args.pr_link)
        analysis_text = analyze_diff_with_deepseek(diff_text)
        pr_report = generate_formatted_pr_report(diff_text, analysis_text, args.target, args.pr_link)
        
        pyperclip.copy(pr_report)
        print("\n📋 Generated PR report copied to clipboard!\n")
        console.print(Markdown(pr_report))
    except Exception as e:
        print(f"🚫 Error: {e}")

if __name__ == "__main__":
    main()
