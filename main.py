import argparse
import os
import pyperclip
import traceback
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import questionary
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables.
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY environment variable")

# Import GitHub helper functions and tools.
from tools.github_utils import get_pr_diff, fetch_current_description, update_pr_description
from tools.github_tools import analyze_diff as github_analyze_diff, generate_report as github_generate_report

# Import YouTube tools.
from tools.youtube_tools import analyze_video, generate_video_tags

def run_github(pr_link: str, target: str):
    console = Console()
    try:
        console.print("🚀 Starting GitHub PR report generation process...\n")
        diff_text = get_pr_diff(pr_link)
        
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"
        )
        
        analysis = github_analyze_diff(diff=diff_text, llm=llm)
        pr_report = github_generate_report(diff=diff_text, analysis=analysis, pr_link=pr_link, target=target, llm=llm)
        
        pyperclip.copy(pr_report)
        console.print("\n📋 Generated PR report copied to clipboard!\n")
        console.print(Markdown(pr_report))
        
        current_desc = fetch_current_description(pr_link)
        console.print(Panel(current_desc, title="Current PR Description", expand=False))
        
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

def run_youtube(video: str, language: str, target: str, prompt_only: bool, dynamic_tags: bool):
    console = Console()
    try:
        console.print("🚀 Starting YouTube video analysis process...\n")
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"
        )
        analysis_result = analyze_video(video_url=video, language=language, target=target, prompt_only=prompt_only, llm=llm)
        video_title = analysis_result.get("video_title", "Untitled Video")
        if prompt_only:
            output_body = analysis_result.get("prompt")
        else:
            output_body = analysis_result.get("analysis")
        
        if target.lower() == "markdown" and (not prompt_only) and dynamic_tags:
            tags = generate_video_tags(analysis_text=output_body, llm=llm)
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
{tags}
---
"""
        else:
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
  - youtube
  - video analysis
  - transcript
  - smolagents
---
"""
        if target.lower() == "markdown":
            final_output = metadata + "\n" + output_body
        else:
            final_output = output_body
        
        pyperclip.copy(final_output)
        console.print(Panel(f"Video Title: {video_title}", title="Video Analysis", expand=False))
        console.print(Markdown("=== Video Analysis Output ==="))
        console.print(Markdown(final_output))
    except Exception as e:
        console.print(f"🚫 Error: {e}")
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(
        description="Unified tool for GitHub PR analysis and YouTube video analysis using smolagents."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Choose a subcommand to run.")

    # GitHub subcommand.
    github_parser = subparsers.add_parser("github", help="Generate a PR report for a GitHub pull request.")
    github_parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    github_parser.add_argument("--target", choices=["github", "slack"], default="github", help="Output format target (default: github)")

    # YouTube subcommand.
    youtube_parser = subparsers.add_parser("youtube", help="Generate a transcript analysis for a YouTube video.")
    youtube_parser.add_argument("video", help="YouTube video ID or URL")
    youtube_parser.add_argument("--language", default="en", help="Language code (default: en)")
    youtube_parser.add_argument("--target", choices=["markdown", "slack"], default="markdown", help="Output format option (default: markdown)")
    youtube_parser.add_argument("--prompt-only", action="store_true", help="Generate the prompt only without invoking the LLM")
    youtube_parser.add_argument("--dynamic-tags", action="store_true", help="Generate dynamic tags based on the analysis output")
    
    args = parser.parse_args()

    if args.command == "github":
        run_github(pr_link=args.pr_link, target=args.target)
    elif args.command == "youtube":
        run_youtube(video=args.video, language=args.language, target=args.target, prompt_only=args.prompt_only, dynamic_tags=args.dynamic_tags)

if __name__ == "__main__":
    main()
