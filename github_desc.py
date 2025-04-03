import os
import argparse
import pyperclip
import requests
from github import Github
from openai import OpenAI as DeepseekClient

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN environment variable not set")
if not DEEPSEEK_API_KEY:
    raise Exception("DEEPSEEK_API_KEY environment variable not set")

def get_pr_diff(pr_url):
    """
    Uses PyGithub to fetch the diff (patch) for a pull request from a private repository.
    Expected PR URL format: https://github.com/{owner}/{repo}/pull/{pr_number}
    """
    g = Github(GITHUB_TOKEN)
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 7:
        raise Exception("Invalid PR URL format")
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
        raise Exception(f"Error fetching diff: {response.status_code} {response.text}")
    return response.text

def analyze_diff_with_deepseek(diff_text):
    """
    Uses the Deepseek client to analyze the diff.
    """
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a code analysis assistant."},
            {"role": "user", "content": diff_text}
        ],
        stream=False
    )
    return response.choices[0].message.content

def generate_description(diff_text, analysis_text):
    """
    Uses the Deepseek client to generate a formatted change description based on the code diff and analysis.
    The output follows a template with sections for Title, Description, Why, and Risks.
    """
    prompt_template = """
You are an assistant that summarizes code changes. Based on the provided code diff and analysis, generate a change description following this template:
<TEMPLATE_START>
## Title
{title}

## Description :memo:
{description}

## Why? :white_check_mark:
{why}

## Risks? :warning:
{risks}

### Code Diff:
{diff_text}

### Analysis:
{analysis_text}
<TEMPLATE_END>

Fill in the sections appropriately, ensuring that the output is clear and formatted as shown.
The output should contain only the section described above within <TEMPLATE_START><TEMPLATE_END>
"""
    filled_prompt = prompt_template.format(
        title="Enter the PR title here (e.g. Brief title of changes)",
        description="Summarize the introduced changes and key updates.",
        why="Explain the motivation behind these changes, such as improvements in performance or maintainability.",
        risks="List any potential risks like integration issues or side effects.",
        diff_text=diff_text,
        analysis_text=analysis_text
    )
    
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates formatted PR descriptions."},
            {"role": "user", "content": filled_prompt}
        ],
        stream=False
    )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted PR description using Deepseek and GitHub API"
    )
    parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    args = parser.parse_args()

    try:
        diff_text = get_pr_diff(args.pr_link)
        analysis_text = analyze_diff_with_deepseek(diff_text)
        full_description = generate_description(diff_text, analysis_text)
        pyperclip.copy(full_description)
        
        print("Generated description copied to clipboard:")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

