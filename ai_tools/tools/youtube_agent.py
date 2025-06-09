import os
import re
import pyperclip
import traceback
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from tools.youtube_tools import analyze_video, generate_video_tags
from tools.slack_tools import post_to_slack, format_for_slack, extract_youtube_from_slack_thread, extract_youtube_from_slack_channel
from tools.youtube_utils import extract_video_id
from tools.llm_config import get_llm

def get_youtube_url_from_user(console):
    """Get a valid YouTube URL from user input with validation."""
    while True:
        video_url = Prompt.ask(
            Text("📺 Please paste the YouTube URL from Slack", style="bold cyan"),
            console=console,
            default="",
            show_default=False
        ).strip()
        
        if not video_url:
            console.print("[red]❌ YouTube URL is required to proceed[/red]")
            continue
            
        # Validate YouTube URL format
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        is_valid = any(re.match(pattern, video_url) for pattern in youtube_patterns)
        
        if is_valid:
            console.print(Panel.fit(
                f"✅ Valid YouTube URL: [link]{video_url}[/link]",
                border_style="green",
                title="[bold green]URL Accepted[/bold green]"
            ))
            return video_url
        else:
            console.print(Panel.fit(
                f"❌ Invalid YouTube URL format\n\n"
                f"Expected formats:\n"
                f"• https://www.youtube.com/watch?v=VIDEO_ID\n"
                f"• https://youtu.be/VIDEO_ID",
                border_style="red",
                title="[bold red]Invalid URL[/bold red]"
            ))
            console.print(f"[dim]You entered: {video_url}[/dim]")
            continue

def run_youtube(
    video: Optional[str],
    language: str,
    target: str,
    prompt_only: bool,
    dynamic_tags: bool,
    slack_thread_url: Optional[str] = None,
    slack_channel_name: Optional[str] = None,
    ask_for_url: bool = False,
    llm_provider: str = "anthropic" # Added llm_provider argument with default
):
    console = Console()
    try:
        # Validate inputs
        if target.lower() == "slack" and not slack_thread_url and not slack_channel_name:
            raise ValueError("Either Slack thread URL or channel name is required when target is 'slack'")
        
        # Handle manual URL input for Slack permission workaround
        if not video and ask_for_url and target.lower() == "slack":
            console.print()
            console.print(Panel.fit(
                "[cyan]🔗 YouTube URL Input Required[/cyan]\n\n"
                "Due to Slack permission limitations, please manually provide the YouTube URL.",
                title="[bold yellow]Manual Input Needed[/bold yellow]",
                border_style="yellow"
            ))
            
            video = get_youtube_url_from_user(console)
        
        # Auto-extract YouTube URL from Slack if video not provided
        if not video and target.lower() == "slack":
            extracted_video = None
            
            if slack_channel_name:
                console.print(f"🔍 Extracting YouTube URL from Slack channel: {slack_channel_name}...")
                extracted_video = extract_youtube_from_slack_channel(slack_channel_name)
            elif slack_thread_url:
                console.print("🔍 Extracting YouTube URL from Slack thread...")
                extracted_video = extract_youtube_from_slack_thread(slack_thread_url)
            
            # Handle special return values
            if extracted_video == "MANUAL_INPUT_REQUESTED":
                # User chose to input manually after permission error
                console.print()
                console.print(Panel.fit(
                    "[cyan]🔗 Manual YouTube URL Input[/cyan]\n\n"
                    "Please provide the YouTube URL from the Slack message.",
                    title="[bold yellow]Input Required[/bold yellow]",
                    border_style="yellow"
                ))
                
                video = get_youtube_url_from_user(console)
                
            elif extracted_video:
                video = extracted_video
                console.print(f"✅ Found YouTube URL: {video}")
            else:
                # No URL found and user didn't request manual input
                source = "channel" if slack_channel_name else "thread"
                raise ValueError(f"No YouTube URL found in the Slack {source}")
        
        if not video:
            raise ValueError("YouTube URL is required. Provide it as argument or ensure it exists in the Slack thread.")
            
        if not video.startswith(("http", "www.youtube")):
            raise ValueError("Please provide a full YouTube URL")

        # Extract video ID from URL
        video_id = extract_video_id(video)
        if not video_id or len(video_id) != 11:
            raise ValueError(f"Invalid YouTube URL: {video}")

        # Initialize LLM using the centralized configuration function.
        # The provider is passed from the command line argument.
        llm = get_llm(llm_provider)
        
        # Run analysis - let the analyze_video function handle its own progress
        console.print("🚀 Starting YouTube video analysis...")
        
        analysis_result = analyze_video(
            video_url=video,
            language=language,
            target=target,
            prompt_only=prompt_only,
            llm=llm # Pass the initialized LLM
        )
        
        console.print()  # Add spacing after progress
        
        video_title = analysis_result.get("video_title", "Untitled Video")
        output_body = analysis_result.get("prompt") if prompt_only else analysis_result.get("analysis")

        # Check if analysis failed - don't proceed with Slack posting if there's an error
        if output_body and output_body.startswith("Error:"):
            console.print(f"[red]🚫 {output_body}[/red]")
            
            # Special handling for user declined input
            if "user declined manual input" in output_body:
                console.print("[dim]Operation cancelled by user choice.[/dim]")
                return {
                    "video_title": video_title,
                    "status": "cancelled",
                    "message": "User chose not to provide manual transcript"
                }
            else:
                return {
                    "video_title": video_title,
                    "status": "failed",
                    "error": output_body
                }

        # Check if we have valid content to post
        if not output_body or len(output_body.strip()) == 0:
            console.print("[red]🚫 No content generated for analysis[/red]")
            return {
                "video_title": video_title,
                "status": "failed", 
                "error": "No content generated"
            }

        # Handle output based on target
        if target.lower() == "slack":
            # Clean content for Slack
            cleaned_content = output_body
            
            # Remove common analysis headers and titles
            cleaned_content = re.sub(r'\*\*Video Analysis:\*\*.*?\n', '', cleaned_content, flags=re.DOTALL)
            cleaned_content = re.sub(r'^\*.*?\*\s*\n\n', '', cleaned_content, flags=re.MULTILINE)  # Remove title lines
            cleaned_content = re.sub(re.escape(video), '', cleaned_content)  # Remove URL
            cleaned_content = re.sub(re.escape(video_title), '', cleaned_content)  # Remove title text
            
            # Clean markdown formatting for Slack
            slack_content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', cleaned_content)  # Bold
            slack_content = re.sub(r'__([^_]+)__', r'_\1_', slack_content)      # Italic  
            slack_content = re.sub(r'^-{3,}$', '', slack_content, flags=re.MULTILINE)  # Horizontal rules
            slack_content = re.sub(r'\n{3,}', '\n\n', slack_content)  # Multiple newlines
            
            formatted_slack = format_for_slack(slack_content, "analysis")
            
            # Post to Slack thread
            slack_result = post_to_slack(
                content=formatted_slack,
                slack_link=slack_thread_url,
                title=video_title,
                content_type="analysis"
            )
            
            # Only report success if the operation actually succeeded
            if slack_result.get("success", False):
                console.print(f"[green]✅ Successfully posted to Slack thread[/green]")
                return {
                    "video_title": video_title,
                    "status": "success",
                    "slack_result": slack_result
                }
            else:
                error_msg = slack_result.get("error", "Unknown error")
                console.print(f"[red]🚫 Failed to post to Slack: {error_msg}[/red]")
                return {
                    "video_title": video_title,
                    "status": "failed",
                    "error": error_msg
                }
            
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
            
            return {
                "video_title": video_title,
                "status": "success",
                "content": final_output
            }

    except ValueError as e:
        console.print(f"[red]🚫 Validation Error: {e}[/red]")
        if "Slack thread URL" in str(e):
            console.print("When using --target slack, you must provide:")
            console.print("  --slack-thread 'https://.../archives/CHANNEL_ID/pTIMESTAMP'")
    except Exception as e:
        console.print(f"[red]🚫 Error: {e}[/red]")
        traceback.print_exc()

