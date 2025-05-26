import os
import re
import pyperclip
import traceback
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from tools.youtube_tools import analyze_video, generate_video_tags
from tools.slack_tools import post_to_slack, format_for_slack
from tools.youtube_utils import extract_video_id
from tools.llm_config import get_llm

def run_youtube(
    video: str,
    language: str,
    target: str,
    prompt_only: bool,
    dynamic_tags: bool,
    slack_thread_url: Optional[str] = None,
    llm_provider: str = "anthropic" # Added llm_provider argument with default
):
    console = Console()
    try:
        # Validate inputs
        if target.lower() == "slack" and not slack_thread_url:
            raise ValueError("Slack thread URL is required when target is 'slack'")
            
        if not video.startswith(("http", "www.youtube")):
            raise ValueError("Please provide a full YouTube URL")

        console.print("🚀 Starting YouTube video analysis...\n")
        
        # Extract video ID from URL
        video_id = extract_video_id(video)
        if not video_id or len(video_id) != 11:
            raise ValueError(f"Invalid YouTube URL: {video}")

        # Initialize LLM using the centralized configuration function.
        # The provider is passed from the command line argument.
        llm = get_llm(llm_provider)
        
        # Run analysis
        analysis_result = analyze_video(
            video_url=video,
            language=language,
            target=target,
            prompt_only=prompt_only,
            llm=llm # Pass the initialized LLM
        )
        
        video_title = analysis_result.get("video_title", "Untitled Video")
        output_body = analysis_result.get("prompt") if prompt_only else analysis_result.get("analysis")

        # Handle output based on target
        if target.lower() == "slack":
            # Clean and format content
            cleaned_content = re.sub(
                r'\*\*Video Analysis:\*\*.*?\n', 
                '', 
                output_body, 
                flags=re.DOTALL
            )
            cleaned_content = re.sub(
                re.escape(video), 
                '', 
                cleaned_content
            )
            
            # Build Slack message structure
            slack_content = f"*{video_title}*\n\n{cleaned_content}"
            
            # Remove residual markdown artifacts
            slack_content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', slack_content)
            slack_content = re.sub(r'__([^_]+)__', r'_\1_', slack_content)
            slack_content = re.sub(r'^-{3,}$', '', slack_content, flags=re.MULTILINE)
            
            formatted_slack = format_for_slack(slack_content, "analysis")
            
            # Post to Slack thread
            post_to_slack(
                content=formatted_slack,
                slack_link=slack_thread_url,
                title=video_title,
                content_type="analysis"
            )
            console.print(f"[green]✅ Successfully posted to Slack thread[/green]")
            
        else: # markdown output
            # Generate Markdown output
            if dynamic_tags and not prompt_only:
                tags = generate_video_tags(output_body, llm) # Pass the initialized LLM
                metadata = f"""---
title: {video_title}
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
        console.print(f"[red]🚫 Validation Error: {e}[/red]")
        if "Slack thread URL" in str(e):
            console.print("When using --target slack, you must provide:")
            console.print("  --slack-thread 'https://.../archives/CHANNEL_ID/pTIMESTAMP'")
    except Exception as e:
        console.print(f"[red]🚫 Error: {e}[/red]")
        traceback.print_exc()

