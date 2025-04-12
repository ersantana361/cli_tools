import os
import argparse
import pyperclip
import requests
from github import Github
from rich.console import Console
from rich.markdown import Markdown

# Import the prompt template and ChatOpenAI using the new modules.
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Check required environment variables.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not GITHUB_TOKEN:
    raise Exception("🚫 GITHUB_TOKEN environment variable not set")
if not DEEPSEEK_API_KEY:
    raise Exception("🚫 DEEPSEEK_API_KEY environment variable not set")


def get_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff (patch) for a pull request from a private repository
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


def build_pipeline(llm: ChatOpenAI, target: str):
    """
    Constructs a sequential pipeline that:
      1. Analyzes the diff.
      2. Generates a formatted PR report using the analysis and diff.

    Both steps are built by chaining PromptTemplates with the LLM via the new operator (|).
    """

    # Define the analysis prompt template.
    analysis_template = (
        "You are a code analysis assistant. Analyze the following diff and summarize your key findings:\n\n"
        "{diff}"
    )
    analysis_prompt = PromptTemplate(
        input_variables=["diff"],
        template=analysis_template
    )
    # Compose the analysis chain.
    analysis_chain = analysis_prompt | llm

    # Define the report prompt template based on target formatting.
    if target.lower() == "slack":
        report_section = (
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
        report_section = (
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

    report_template = (
        "You are an assistant that summarizes code changes for a pull request. Based on the provided diff and analysis, "
        "generate a report using the following structure:\n\n"
        f"{report_section}\n\n"
        "Diff:\n"
        "{diff}\n\n"
        "Analysis:\n"
        "{analysis}"
    )
    report_prompt = PromptTemplate(
        input_variables=["diff", "analysis", "pr_link"],
        template=report_template
    )
    # Compose the report chain.
    report_chain = report_prompt | llm

    def pipeline(inputs: dict) -> str:
        # First, run analysis on the diff.
        print("🤖 Starting analysis of the diff. This may take a moment...")
        analysis_result = analysis_chain.invoke({"diff": inputs["diff"]})
        # Ensure the output is a string.
        if hasattr(analysis_result, "content"):
            analysis_result = analysis_result.content
        print("✅ Analysis complete!")

        # Now, use the analysis to generate the final report.
        print("📝 Generating formatted PR report. Please wait...")
        report_input = {
            "diff": inputs["diff"],
            "analysis": analysis_result,
            "pr_link": inputs["pr_link"]
        }
        report_result = report_chain.invoke(report_input)
        if hasattr(report_result, "content"):
            report_result = report_result.content
        print("✅ PR report generation complete!")
        return report_result

    return pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Generate a formatted PR report using LangChain, Deepseek, and GitHub API"
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

        # Initialize the LLM using the updated ChatOpenAI from langchain-openai.
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"  # Custom base URL if needed.
        )

        # Build the chained pipeline.
        pipeline = build_pipeline(llm, args.target)
        chain_inputs = {"diff": diff_text, "pr_link": args.pr_link}
        pr_report = pipeline(chain_inputs)

        # Copy report to clipboard and print to console.
        pyperclip.copy(pr_report)
        print("\n📋 Generated PR report copied to clipboard!\n")
        console.print(Markdown(pr_report))
    except Exception as e:
        print(f"🚫 Error: {e}")


if __name__ == "__main__":
    main()
