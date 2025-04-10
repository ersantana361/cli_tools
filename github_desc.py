import os
import argparse
import pyperclip
import requests
from github import Github
from openai import OpenAI as DeepseekClient

# Check for required environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not GITHUB_TOKEN:
    raise Exception("🚫 GITHUB_TOKEN environment variable not set")
if not DEEPSEEK_API_KEY:
    raise Exception("🚫 DEEPSEEK_API_KEY environment variable not set")

def get_pr_diff(pr_url):
    """
    Uses PyGithub to fetch the diff (patch) for a pull request from a private repository.
    Expected PR URL format: https://github.com/{owner}/{repo}/pull/{pr_number}
    """
    print("🔍 Fetching PR diff from GitHub...")
    
    # Initialize GitHub client with token
    g = Github(GITHUB_TOKEN)
    
    # Parse the PR URL to extract owner, repo, and PR number
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 7:
        raise Exception("🚫 Invalid PR URL format")
    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])
    
    # Get the repository and the pull request details
    repository = g.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    
    # Construct API URL and headers to fetch the diff
    api_url = pr.url
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    # Request the diff from GitHub
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"🚫 Error fetching diff: {response.status_code} {response.text}")
    
    print("✅ PR diff fetched successfully!")
    return response.text

def analyze_diff_with_deepseek(diff_text):
    """
    Uses the Deepseek client to analyze the diff.
    """
    print("🤖 Analyzing diff with Deepseek...")
    
    # Initialize Deepseek client with API key and endpoint URL
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    
    # Call Deepseek's chat completion API with the diff text
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

def generate_description(diff_text, analysis_text):
    """
    Uses the Deepseek client to generate a formatted change description based on the code diff and analysis.
    The output follows a template with sections for Title, Description, Why, and Risks.
    """
    print("📝 Generating formatted PR description with Deepseek...")
    
    # Define the template for the PR description
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
        analysis_text=analysis_text
    )
    
    # Initialize Deepseek client and generate the description using the filled prompt
    client = DeepseekClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates formatted PR descriptions."},
            {"role": "user", "content": filled_prompt}
        ],
        stream=False
    )
    
    print("✅ Formatted description generated!")
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted PR description using Deepseek and GitHub API"
    )
    parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    args = parser.parse_args()

    print("🚀 Starting PR description generation process...")
    try:
        # Step 1: Fetch the diff from the PR
        diff_text = get_pr_diff(args.pr_link)
        
        # Step 2: Analyze the diff using Deepseek
        analysis_text = analyze_diff_with_deepseek(diff_text)
        
        # Step 3: Generate the formatted description using the diff and analysis
        full_description = generate_description(diff_text, analysis_text)
        
        # Step 4: Copy the generated description to clipboard
        pyperclip.copy(full_description)
        print("📋 Generated description copied to clipboard!")
    except Exception as e:
        print(f"🚫 Error: {e}")

if __name__ == "__main__":
    main()
