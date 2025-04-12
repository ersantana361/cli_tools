import argparse
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.markdown import Markdown
import pyperclip

# Load environment variables.
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
if not YOUTUBE_API_KEY:
    raise Exception("Missing YOUTUBE_API_KEY environment variable")
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY environment variable")


def extract_video_id(url):
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


def get_video_title(video_id):
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


def format_time(seconds_float):
    """
    Formats a floating point number (in seconds) into MM:SS format.
    """
    seconds = int(seconds_float)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


def generate_dynamic_tags(analysis_text, llm):
    """
    Uses LangChain to generate dynamic tags based on the provided analysis text.
    Returns a YAML-formatted list of tags without any markdown code fences.
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
    tag_prompt = PromptTemplate(input_variables=[], template=prompt_text)
    tag_chain = tag_prompt | llm
    tags_result = tag_chain.invoke({})
    if hasattr(tags_result, "content"):
        tags_result = tags_result.content
    # Remove any code fences such as "```yaml" or "```".
    tags_result = tags_result.replace("```yaml", "").replace("```", "").strip()
    console.print("[green]Dynamic tags generation complete.[/green]")
    return tags_result


def generate_video_analysis(video_url, language, target, prompt_only=False):
    """
    Generates the full analysis prompt for a YouTube video transcript.
    If prompt_only is True, returns the generated prompt text without invoking the LLM.
    Otherwise, sends the prompt to the LLM via LangChain and returns the analysis result.
    """
    console = Console()
    console.print("[bold green]🚀 Starting video analysis process...[/bold green]")
    
    # Extract video ID and fetch video title.
    video_id = extract_video_id(video_url)
    console.print("[green]Extracting video ID...[/green]")
    video_title = get_video_title(video_id)
    console.print(f"[green]Fetched video title:[/green] {video_title}")
    
    video_base_url = f"https://youtu.be/{video_id}"
    
    # Fetch the transcript.
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
    transcript_entries_text = "\n".join(transcript_entries)
    
    # Build the analysis prompt.
    console.print("[green]Building analysis prompt...[/green]")
    if target.lower() == "slack":
        # Slack-friendly formatting.
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
{transcript_entries_text}
[TRANSCRIPT END]
"""
    else:
        # Default: Markdown formatting.
        prompt_text = f"""
**Video Analysis Request**

Analyze this YouTube video transcript and provide a detailed breakdown.

### **Introduction**
- **Title**: [{video_title}]({video_url})
- **Overview**: Provide a comprehensive explanation of the video's key objectives and themes.

### **Chronological Analysis**
For each significant segment:
- Identify section titles and timestamps.
- Present 1-2 verbatim excerpts from the transcript.
- Provide detailed technical analysis.

### **Conclusion**
Summarize the video's progression, highlighting key milestones and learning outcomes.

**Requirements**:
- Maintain strict chronological order.
- Blend direct quotes with detailed analysis.
- Output language: {language}

YouTube Link: {video_url}

[TRANSCRIPT START]
{transcript_entries_text}
[TRANSCRIPT END]
"""
    
    # If prompt-only mode is enabled, return the prompt text.
    if prompt_only:
        console.print("[green]Prompt-only mode enabled. Returning generated prompt without invoking LLM.[/green]")
        return prompt_text, video_title

    # Create a LangChain prompt template using the complete prompt.
    analysis_prompt = PromptTemplate(input_variables=[], template=prompt_text)
    
    # Initialize the ChatOpenAI instance.
    console.print("[green]Initializing LLM via LangChain...[/green]")
    llm = ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com"
    )
    
    # Chain the prompt with the LLM.
    console.print("[green]Sending prompt to LLM for analysis...[/green]")
    analysis_chain = analysis_prompt | llm
    result = analysis_chain.invoke({})
    if hasattr(result, "content"):
        result = result.content
    console.print("[green]Analysis complete.[/green]")
    
    return result, video_title


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a detailed YouTube video transcript analysis using LangChain."
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
    
    # Generate analysis result or prompt.
    analysis_output, video_title = generate_video_analysis(args.video, args.language, args.target, args.prompt_only)
    
    # Prepare metadata for Markdown output.
    if args.target.lower() == "markdown":
        if not args.prompt_only and args.dynamic_tags:
            # Generate dynamic tags if enabled and analysis was performed.
            llm_for_tags = ChatOpenAI(
                api_key=DEEPSEEK_API_KEY,
                model_name="deepseek-chat",
                base_url="https://api.deepseek.com"
            )
            dynamic_tags = generate_dynamic_tags(analysis_output, llm_for_tags)
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
{dynamic_tags}
---
"""
        else:
            # Use static tags.
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
  - youtube
  - video analysis
  - transcript
  - langchain
---
"""
        final_output = metadata + "\n" + analysis_output
    else:
        final_output = analysis_output

    # Copy the final output to the clipboard.
    pyperclip.copy(final_output)
    
    # Pretty-print the final output using Rich Markdown.
    console = Console()
    console.print(Markdown("=== Video Analysis Output ==="))
    console.print(Markdown(final_output))
