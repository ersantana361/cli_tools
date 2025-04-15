import os
import argparse
import pyperclip
import requests
from github import Github
from rich.console import Console
from rich.markdown import Markdown
import questionary
import traceback

# Use the updated ChatOpenAI from langchain_openai.
from langchain_openai import ChatOpenAI

# Import the tool decorator from smolagents.
from smolagents import tool


def get_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff (patch) for a pull request from a private repository.
    Expected PR URL format: https://github.com/{owner}/{repo}/pull/{pr_number}
    """
    print("🔍 Fetching PR diff from GitHub...")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_WORK")
    if not GITHUB_TOKEN:
        raise Exception("🚫 GITHUB_TOKEN_WORK environment variable not set")
        
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


@tool
def analyze_diff(diff: str, llm: ChatOpenAI) -> str:
    """
    Analyzes the diff and summarizes key findings.

    Args:
        diff: The diff text to analyze.
        llm: The ChatOpenAI instance to use for analysis.
    Returns:
        A summary of key findings as a string.
    """
    prompt = (
        "You are a code analysis assistant. Analyze the following diff and summarize your key findings:\n\n"
        f"{diff}"
    )
    print("🤖 Starting analysis of the diff. This may take a moment...")
    # Pass the prompt string directly instead of a dictionary.
    result = llm.invoke(prompt)
    analysis = result.content if hasattr(result, "content") else result
    print("✅ Analysis complete!")
    return analysis


@tool
def generate_report(diff: str, analysis: str, pr_link: str, target: str, llm: ChatOpenAI) -> str:
    """
    Generates the final PR report based on the diff and analysis.

    Args:
        diff: The full diff text.
        analysis: The analysis summary.
        pr_link: The GitHub PR link.
        target: The output format target ("github" or "slack").
        llm: The ChatOpenAI instance to use for report generation.
    Returns:
        The generated PR report as a string.
    """
    if target.lower() == "slack":
        report_template = (
            "Guys, please review the following PR.\n\n"
            "*PR Link:* <{pr_link}>\n\n"
            "*Description:*  \n"
            "[Summarize the changes and key updates.]\n\n"
            "*Why:*  \n"
            "[Explain the reasoning and motivation behind the changes.]\n\n"
            "*Risks:*  \n"
            "[List any potential risks or side effects.]\n\n"
            "*Code Snippets & Explanation:*  \n"
            "[Extract and explain relevant code snippet(s) from the diff; if including code, wrap it in triple backticks (```)]."
        )
    else:
        report_template = (
            "## Description 📝\n"
            "[Summarize the changes and key updates.]\n\n"
            "## Why? ✅\n"
            "[Explain the reasoning and motivation behind the changes.]\n\n"
            "## Risks? ⚠️\n"
            "[List any potential risks or side effects.]\n\n"
            "## Code Snippets & Explanation 📑\n"
            "[Extract and explain relevant code snippet(s) from the diff; if including code, wrap it in triple backticks (```)].\n\n"
            "PR Link: {pr_link}"
        )
    report_template = report_template.format(pr_link=pr_link)
    report_prompt = (
        "You are an assistant that summarizes code changes for a pull request. Based on the provided diff and analysis, "
        "generate a report using the following structure:\n\n"
        f"{report_template}\n\n"
        "Diff:\n"
        f"{diff}\n\n"
        "Analysis:\n"
        f"{analysis}"
    )
    print("📝 Generating formatted PR report. Please wait...")
    # Pass the prompt string directly.
    result = llm.invoke(report_prompt)
    pr_report = result.content if hasattr(result, "content") else result
    print("✅ PR report generation complete!")
    return pr_report


def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted PR report using smolagents, Deepseek, and the GitHub API"
    )
    parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    parser.add_argument(
        "--target",
        choices=["github", "slack"],
        default="github",
        help="Output format target (default: github)"
    )
    args = parser.parse_args()

    console = Console()
    try:
        print("🚀 Starting PR report generation process...\n")
        diff_text = get_pr_diff(args.pr_link)

        # Initialize the LLM using ChatOpenAI from langchain_openai.
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        if not DEEPSEEK_API_KEY:
            raise Exception("🚫 DEEPSEEK_API_KEY environment variable not set")
            
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"  # Custom base URL if needed.
        )

        # Run the analysis tool.
        analysis = analyze_diff(diff=diff_text, llm=llm)
        # Run the report generation tool.
        pr_report = generate_report(
            diff=diff_text,
            analysis=analysis,
            pr_link=args.pr_link,
            target=args.target,
            llm=llm
        )

        # Copy report to clipboard and print it to the console.
        pyperclip.copy(pr_report)
        print("\n📋 Generated PR report copied to clipboard!\n")
        console.print(Markdown(pr_report))

        # Prompt the user to update the PR description.
        update_choice = questionary.confirm("Do you want to update the PR description with this report?").ask()
        if update_choice:
            print("🔄 Updating the PR description with the generated report...")
            GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_WORK")
            if not GITHUB_TOKEN:
                raise Exception("🚫 GITHUB_TOKEN_WORK environment variable not set")
            g = Github(GITHUB_TOKEN)
            parts = args.pr_link.rstrip("/").split("/")
            owner = parts[3]
            repo = parts[4]
            pr_number = int(parts[6])
            repository = g.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            pr.edit(body=pr_report)
            print("✅ PR description updated successfully!")
        else:
            print("ℹ️ PR description not updated.")

    except Exception as e:
        print(traceback.format_exc())
        print(f"🚫 Error: {e}")


if __name__ == "__main__":
    main()