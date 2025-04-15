import argparse
import os
import re
import pyperclip
import traceback
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Use the updated ChatOpenAI from langchain_openai.
from langchain_openai import ChatOpenAI

# Import the tool decorator from smolagents.
from smolagents import tool

# Load environment variables.
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
if not YOUTUBE_API_KEY:
    raise Exception("Missing YOUTUBE_API_KEY environment variable")
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY environment variable")


def extract_video_id(url: str) -> str:
    """
    Extracts the video ID from a YouTube URL or a direct ID input.
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url


def get_video_title(video_id: str) -> str:
    """
    Fetches the video title from the YouTube API given a video ID.
    """
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        return response['items'][0]['snippet']['title']
    except Exception as e:
        print(f"Could not fetch title: {e}")
        return "Untitled Video"


def format_time(seconds_float: float) -> str:
    """
    Formats a floating point number (in seconds) into MM:SS format.
    """
    seconds = int(seconds_float)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


@tool
def analyze_video(video_url: str, language: str, target: str, prompt_only: bool, llm: ChatOpenAI) -> dict:
    """
    Analyzes a YouTube video transcript and produces an analysis or prompt.

    Args:
        video_url: The YouTube video URL or ID.
        language: Transcript language code (e.g. "en").
        target: Output format option ("markdown" or "slack").
        prompt_only: If True, returns the generated prompt text without invoking the LLM.
        llm: The ChatOpenAI instance to use for analysis.
    Returns:
        A dictionary with keys:
          - "video_title": Title of the video.
          - "analysis": Analysis output (if prompt_only is False) or
          - "prompt": Generated prompt (if prompt_only is True).
    """
    console = Console()
    console.print("[green]Extracting video ID...[/green]")
    video_id = extract_video_id(video_url)
    video_title = get_video_title(video_id)
    console.print(f"[green]Fetched video title:[/green] {video_title}")
    
    video_base_url = f"https://youtu.be/{video_id}"
    
    console.print("[green]Fetching video transcript...[/green]")
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
    if not transcript:
        raise Exception("No transcript found.")
    console.print("[green]Transcript fetched successfully.[/green]")
    
    transcript_entries = []
    for entry in transcript:
        start_time = entry['start']
        formatted_time = format_time(start_time)
        link = f"{video_base_url}?t={int(start_time)}"
        transcript_entries.append(f"{formatted_time} (Link: {link}): {entry['text']}")
    transcript_text = "\n".join(transcript_entries)
    
    console.print("[green]Building analysis prompt...[/green]")
    if target.lower() == "slack":
        prompt_text = f"""
*Video Analysis Request*

Analyze this YouTube video transcript and provide a detailed breakdown in Slack-friendly format.

*Introduction*
- *Title*: <{video_url}|{video_title}>
- *Overview*: Provide a comprehensive explanation of the video's key objectives and themes.

*Chronological Analysis*
For each significant segment:
- Identify section titles and timestamps.
- Present 1-2 verbatim excerpts from the transcript.
- Provide detailed technical analysis.

*Conclusion*
Summarize the video's progression, highlighting key milestones and learning outcomes.

*Requirements*:
- Maintain strict chronological order.
- Blend direct quotes with detailed analysis.
- Output language: {language}

YouTube Link: {video_url}

[TRANSCRIPT START]
{transcript_text}
[TRANSCRIPT END]
"""
    else:
        # Default is Markdown-friendly formatting.
        prompt_text = f"""
**Video Analysis Request**

Analyze this YouTube video transcript and provide a detailed breakdown.

### Introduction
- **Title**: [{video_title}]({video_url})
- **Overview**: Provide a comprehensive explanation of the video's key objectives and themes.

### Chronological Analysis
For each significant segment:
- Identify section titles and timestamps.
- Present 1-2 verbatim excerpts from the transcript.
- Provide detailed technical analysis.

### Conclusion
Summarize the video's progression, highlighting key milestones and learning outcomes.

**Requirements**:
- Maintain strict chronological order.
- Blend direct quotes with detailed analysis.
- Output language: {language}

YouTube Link: {video_url}

[TRANSCRIPT START]
{transcript_text}
[TRANSCRIPT END]
"""
    if prompt_only:
        console.print("[green]Prompt-only mode enabled. Returning generated prompt without invoking LLM.[/green]")
        return {"video_title": video_title, "prompt": prompt_text}
    
    console.print("[green]Sending prompt to LLM for analysis...[/green]")
    # Invoke the LLM with the prompt text.
    result = llm.invoke(prompt_text)
    analysis = result.content if hasattr(result, "content") else result
    console.print("[green]Analysis complete.[/green]")
    return {"video_title": video_title, "analysis": analysis}


@tool
def generate_video_tags(analysis_text: str, llm: ChatOpenAI) -> str:
    """
    Generates dynamic YAML-formatted tags for a video based on its analysis.

    Args:
        analysis_text: The video analysis text.
        llm: The ChatOpenAI instance to use for tag generation.
    Returns:
        A string containing YAML-formatted tags without code fences.
    """
    console = Console()
    console.print("[green]Generating dynamic tags from analysis...[/green]")
    prompt_text = f"""
Based on the following YouTube video analysis, generate a list of relevant tags.
Return the tags as a YAML list (for example:
  - tag1
  - tag2
) without any extra commentary.

Analysis:
{analysis_text}
"""
    result = llm.invoke(prompt_text)
    tags_result = result.content if hasattr(result, "content") else result
    # Remove any code fences.
    tags_result = tags_result.replace("```yaml", "").replace("```", "").strip()
    console.print("[green]Dynamic tags generation complete.[/green]")
    return tags_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a detailed YouTube video transcript analysis using smolagents."
    )
    parser.add_argument('video', help="YouTube video ID or URL")
    parser.add_argument('--language', default='en', help="Language code (default: en)")
    parser.add_argument('--target', choices=["markdown", "slack"], default="markdown",
                        help="Output format option: markdown (default) or slack")
    parser.add_argument('--prompt-only', action="store_true",
                        help="Generate the prompt only without invoking the LLM")
    parser.add_argument('--dynamic-tags', action="store_true",
                        help="Generate dynamic tags based on the analysis output; if not set, static tags will be used")
    args = parser.parse_args()
    
    console = Console()

    # Initialize the ChatOpenAI instance.
    llm = ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com"
    )

    # Run the video analysis tool.
    analysis_result = analyze_video(
        video_url=args.video,
        language=args.language,
        target=args.target,
        prompt_only=args.prompt_only,
        llm=llm
    )
    
    video_title = analysis_result.get("video_title", "Untitled Video")
    if args.prompt_only:
        output_body = analysis_result.get("prompt")
    else:
        output_body = analysis_result.get("analysis")
    
    # If markdown output and dynamic tags flag is set (and we're not in prompt-only mode), generate tags.
    if args.target.lower() == "markdown" and (not args.prompt_only) and args.dynamic_tags:
        dynamic_tags = generate_video_tags(analysis_text=output_body, llm=llm)
        metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
{dynamic_tags}
---
"""
    else:
        metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
  - youtube
  - video analysis
---
"""
    
    if args.target.lower() == "markdown":
        final_output = metadata + "\n" + output_body
    else:
        final_output = output_body

    # Copy the final output to the clipboard.
    pyperclip.copy(final_output)
    
    # Pretty-print the final output using Rich Markdown.
    console.print(Panel(f"Video Title: {video_title}", title="Video Analysis", expand=False))
    console.print(Markdown("=== Video Analysis Output ==="))
    console.print(Markdown(final_output))
