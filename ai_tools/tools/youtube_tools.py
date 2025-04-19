from rich.console import Console
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from smolagents import tool
from tools.youtube_utils import extract_video_id, get_video_title, format_time

@tool
def analyze_video(video_url: str, language: str, target: str, prompt_only: bool, llm: ChatOpenAI) -> dict:
    """
    Analyzes a YouTube video transcript and produces an analysis or prompt.

    Args:
        video_url: YouTube video URL or ID.
        language: Language code (e.g. "en").
        target: Output format ("markdown" or "slack").
        prompt_only: If True, returns the generated prompt without LLM invocation.
        llm: The ChatOpenAI instance to use.
    Returns:
        A dictionary with the video title and either an "analysis" key or a "prompt" key.
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
        formatted = format_time(start_time)
        link = f"{video_base_url}?t={int(start_time)}"
        transcript_entries.append(f"{formatted} (Link: {link}): {entry['text']}")
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
        console.print("[green]Prompt-only mode enabled. Returning prompt without invoking LLM.[/green]")
        return {"video_title": video_title, "prompt": prompt_text}
    
    console.print("[green]Sending prompt to LLM for analysis...[/green]")
    result = llm.invoke(prompt_text)
    analysis = result.content if hasattr(result, "content") else result
    console.print("[green]Analysis complete.[/green]")
    return {"video_title": video_title, "analysis": analysis}

@tool
def generate_video_tags(analysis_text: str, llm: ChatOpenAI) -> str:
    """
    Generates dynamic YAML-formatted tags for a video based on its analysis.

    Args:
        analysis_text: Video analysis text.
        llm: The ChatOpenAI instance to use.
    Returns:
        A string with YAML-formatted tags.
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
    tags = result.content if hasattr(result, "content") else result
    tags = tags.replace("```yaml", "").replace("```", "").strip()
    console.print("[green]Dynamic tags generation complete.[/green]")
    return tags
