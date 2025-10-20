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
from tools.youtube_utils import extract_video_id, is_playlist_url, extract_playlist_videos
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

def sanitize_filename(title: str, max_length: int = 100) -> str:
    """
    Sanitize a video title for use as a filename.

    Args:
        title: Video title to sanitize
        max_length: Maximum length for filename (default: 100)

    Returns:
        Safe filename string
    """
    # Remove or replace invalid characters
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces and multiple dashes with single dash
    safe_title = re.sub(r'[\s_]+', '-', safe_title)
    # Remove leading/trailing dashes and dots
    safe_title = safe_title.strip('-. ')
    # Truncate if too long
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length].rstrip('-. ')
    return safe_title or "untitled-video"

def save_to_markdown_file(content: str, video_title: str, output_file: Optional[str] = None, console: Optional[Console] = None) -> dict:
    """
    Save markdown content to a file.

    Args:
        content: Markdown content to save
        video_title: Video title for default filename
        output_file: Custom output filename (optional)
        console: Rich console for output (optional)

    Returns:
        dict with status and filename
    """
    if console is None:
        console = Console()

    try:
        # Generate filename from title if not provided
        if output_file:
            filename = output_file
        else:
            safe_title = sanitize_filename(video_title)
            filename = f"{safe_title}.md"

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]✅ Saved to: {filename}[/green]")
        return {"success": True, "filename": filename}

    except Exception as e:
        console.print(f"[red]❌ Failed to save file: {e}[/red]")
        return {"success": False, "error": str(e)}

def run_youtube(
    video: Optional[str],
    language: str,
    target: str,
    prompt_only: bool,
    dynamic_tags: bool,
    slack_thread_url: Optional[str] = None,
    slack_channel_name: Optional[str] = None,
    ask_for_url: bool = False,
    llm_provider: str = "anthropic", # Added llm_provider argument with default
    save_file: bool = False, # New parameter to enable file saving
    output_file: Optional[str] = None # Custom output filename
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

            # Save to file if requested
            if save_file:
                save_result = save_to_markdown_file(final_output, video_title, output_file, console)
                if not save_result.get("success"):
                    console.print("[yellow]⚠️ File save failed, but content is in clipboard[/yellow]")

            # Always copy to clipboard for convenience
            pyperclip.copy(final_output)
            console.print(Panel(f"Video Title: {video_title}", title="Analysis Complete", expand=False))
            console.print(Markdown(final_output))

            result = {
                "video_title": video_title,
                "status": "success",
                "content": final_output
            }

            if save_file:
                result["saved_file"] = save_result.get("filename")

            return result

    except ValueError as e:
        console.print(f"[red]🚫 Validation Error: {e}[/red]")
        if "Slack thread URL" in str(e):
            console.print("When using --target slack, you must provide:")
            console.print("  --slack-thread 'https://.../archives/CHANNEL_ID/pTIMESTAMP'")
    except Exception as e:
        console.print(f"[red]🚫 Error: {e}[/red]")
        traceback.print_exc()

def run_youtube_batch(
    video_urls: list,
    language: str = "en",
    target: str = "markdown",
    prompt_only: bool = False,
    dynamic_tags: bool = False,
    llm_provider: str = "anthropic",
    save_file: bool = True,
    output_dir: Optional[str] = None
) -> dict:
    """
    Process multiple YouTube videos in batch.

    Args:
        video_urls: List of YouTube video URLs
        language: Transcript language code
        target: Output format (markdown or slack)
        prompt_only: Generate prompt without LLM analysis
        dynamic_tags: Generate dynamic content tags
        llm_provider: LLM provider to use
        save_file: Save to file (default: True for batch)
        output_dir: Output directory for saved files

    Returns:
        dict with summary of batch processing results
    """
    console = Console()

    # Expand playlists to individual videos
    expanded_urls = []
    for url in video_urls:
        if is_playlist_url(url):
            try:
                console.print(f"[cyan]📋 Extracting videos from playlist: {url}[/cyan]")
                playlist_videos = extract_playlist_videos(url)
                console.print(f"[green]✅ Found {len(playlist_videos)} videos in playlist[/green]")
                expanded_urls.extend(playlist_videos)
            except Exception as e:
                console.print(f"[red]❌ Failed to extract playlist: {e}[/red]")
                continue
        else:
            expanded_urls.append(url)

    if not expanded_urls:
        console.print("[red]❌ No valid video URLs to process[/red]")
        return {"status": "failed", "error": "No valid video URLs"}

    console.print(f"\n[bold cyan]Processing {len(expanded_urls)} video(s)...[/bold cyan]\n")

    results = {
        "total": len(expanded_urls),
        "successful": 0,
        "failed": 0,
        "videos": []
    }

    # Process each video with progress tracking
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Processing videos...", total=len(expanded_urls))

        for idx, video_url in enumerate(expanded_urls, 1):
            try:
                # Update progress description
                progress.update(task, description=f"[cyan]Video {idx}/{len(expanded_urls)}")

                # Process single video
                result = run_youtube(
                    video=video_url,
                    language=language,
                    target=target,
                    prompt_only=prompt_only,
                    dynamic_tags=dynamic_tags,
                    llm_provider=llm_provider,
                    save_file=save_file,
                    output_file=None  # Auto-generate filename from title
                )

                if result.get("status") == "success":
                    results["successful"] += 1
                    video_result = {
                        "url": video_url,
                        "title": result.get("video_title"),
                        "status": "success"
                    }
                    if save_file and "saved_file" in result:
                        video_result["saved_file"] = result["saved_file"]
                    results["videos"].append(video_result)
                else:
                    results["failed"] += 1
                    results["videos"].append({
                        "url": video_url,
                        "title": result.get("video_title", "Unknown"),
                        "status": "failed",
                        "error": result.get("error", "Unknown error")
                    })

                # Update progress
                progress.update(task, advance=1)

                # Brief pause between videos to avoid rate limits
                if idx < len(expanded_urls):
                    import time
                    time.sleep(0.5)

            except Exception as e:
                console.print(f"\n[red]❌ Error processing {video_url}: {e}[/red]\n")
                results["failed"] += 1
                results["videos"].append({
                    "url": video_url,
                    "status": "failed",
                    "error": str(e)
                })
                progress.update(task, advance=1)

    # Print summary
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[bold]Batch Processing Complete[/bold]\n\n"
        f"[green]✅ Successful: {results['successful']}[/green]\n"
        f"[red]❌ Failed: {results['failed']}[/red]\n"
        f"[cyan]📊 Total: {results['total']}[/cyan]",
        title="[bold cyan]Summary[/bold cyan]",
        border_style="cyan"
    ))

    # Show details of failed videos
    if results["failed"] > 0:
        console.print("\n[bold yellow]Failed Videos:[/bold yellow]")
        for video in results["videos"]:
            if video["status"] == "failed":
                console.print(f"  • {video.get('title', video['url'])}")
                if "error" in video:
                    console.print(f"    [dim]Error: {video['error']}[/dim]")

    return results

