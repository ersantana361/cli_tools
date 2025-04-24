import os
import pyperclip
import traceback
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from langchain_openai import ChatOpenAI
from tools.youtube_tools import analyze_video, generate_video_tags
from tools.slack_tools import post_to_slack, format_for_slack
from tools.youtube_utils import extract_video_id

def run_youtube(
    video: str,
    language: str,
    target: str,
    prompt_only: bool,
    dynamic_tags: bool,
    slack_thread_url: Optional[str] = None
):
    console = Console()
    try:
        if target.lower() == "slack" and not slack_thread_url:
            raise ValueError("Slack thread URL is required when target is 'slack'")
            
        if not video.startswith(("http", "www.youtube")):
            raise ValueError("Please provide a full YouTube URL")

        console.print("🚀 Starting YouTube video analysis...\n")
        
        video_id = extract_video_id(video)
        if not video_id or len(video_id) != 11:
            raise ValueError(f"Invalid YouTube URL: {video}")

        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        if not DEEPSEEK_API_KEY:
            raise Exception("Missing DEEPSEEK_API_KEY")
            
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"
        )
        
        analysis_result = analyze_video(
            video_url=video,
            language=language,
            target=target,
            prompt_only=prompt_only,
            llm=llm
        )
        
        video_title = analysis_result.get("video_title", "Untitled Video")
        output_body = analysis_result.get("prompt") if prompt_only else analysis_result.get("analysis")

        if target.lower() == "slack":
            slack_content = f"{output_body}\n\nVideo: {video}"  # Removed title from content
            formatted_slack = format_for_slack(slack_content, "analysis")
            
            post_to_slack(  # Corrected function name
                content=formatted_slack,
                slack_link=slack_thread_url,
                title=video_title,  # Pass title separately
                content_type="analysis"
            )
            console.print(f"[green]✅ Posted to Slack thread: {slack_thread_url}[/green]")
            
        else:
            if dynamic_tags and not prompt_only:
                tags = generate_video_tags(output_body, llm)
                metadata = f"""---
title: {video_title} Analysis
tags:
{tags}
---\n\n"""
            else:
                metadata = f"# {video_title}\n\n"
                
            final_output = metadata + output_body
            pyperclip.copy(final_output)
            console.print(Panel(f"Video Title: {video_title}", title="Analysis Complete", expand=False))
            console.print(Markdown(final_output))

    except ValueError as e:
        console.print(f"[red]🚫 Error: {e}[/red]")
        if "Slack thread URL" in str(e):
            console.print("Usage: --target slack requires --slack-thread <URL>")
    except Exception as e:
        console.print(f"[red]🚫 Error: {e}[/red]")
        traceback.print_exc()
