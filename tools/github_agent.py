import os
import pyperclip
import traceback
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import questionary
from langchain_openai import ChatOpenAI

# Import GitHub helper functions and tools.
from tools.github_utils import get_pr_diff, fetch_current_description, update_pr_description
from tools.github_tools import analyze_diff as github_analyze_diff, generate_report as github_generate_report

def run_github(pr_link: str, target: str):
    console = Console()
    try:
        console.print("🚀 Starting GitHub PR report generation process...\n")
        # Get the PR diff.
        diff_text = get_pr_diff(pr_link)
        
        # Initialize the ChatOpenAI instance.
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        if not DEEPSEEK_API_KEY:
            raise Exception("Missing DEEPSEEK_API_KEY environment variable")
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"
        )
        
        # Run the analysis and then generate the report.
        analysis = github_analyze_diff(diff=diff_text, llm=llm)
        pr_report = github_generate_report(
            diff=diff_text,
            analysis=analysis,
            pr_link=pr_link,
            target=target,
            llm=llm
        )
        
        # Copy report to clipboard and display it.
        pyperclip.copy(pr_report)
        console.print("\n📋 Generated PR report copied to clipboard!\n")
        console.print(Markdown(pr_report))
        
        # Fetch and display the current PR description.
        current_desc = fetch_current_description(pr_link)
        console.print(Panel(current_desc, title="Current PR Description", expand=False))
        
        # Prompt the user for updating the PR.
        update_choice = questionary.confirm("Do you want to update the PR description with the generated report?").ask()
        if update_choice:
            console.print("🔄 Updating the PR description with the generated report...")
            update_pr_description(pr_link, pr_report)
            console.print("✅ PR description updated successfully!")
        else:
            console.print("ℹ️ PR description not updated.")
    except Exception as e:
        console.print(f"🚫 Error: {e}")
        traceback.print_exc()
