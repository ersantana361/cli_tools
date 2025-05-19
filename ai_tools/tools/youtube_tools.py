from rich.console import Console
import re
import traceback # Import the traceback module
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from langchain_openai import ChatOpenAI
from smolagents import tool
# Assuming these are in a file named 'youtube_utils.py' within a 'tools' directory
# and you've confirmed their implementations.
from tools.youtube_utils import extract_video_id, get_video_title, format_time

@tool
def analyze_video(video_url: str, language: str, target: str, prompt_only: bool, llm: ChatOpenAI) -> dict:
    """
    Analyzes a YouTube video transcript and produces structured analysis.
    
    Args:
        video_url: YouTube video URL or ID
        language: Language code (e.g. "en")
        target: Output format ("markdown" or "slack")
        prompt_only: Return prompt without LLM processing
        llm: ChatOpenAI instance
        
    Returns:
        dict: Contains video_title and analysis/prompt or error message
    """
    console = Console()
    video_id = None 
    video_title = "Unknown Title" 
    transcript_text = "" # Initialize transcript_text

    try:
        console.print("[green]Extracting video ID...[/green]")
        video_id = extract_video_id(video_url)
        # It's good to log the extracted ID for debugging:
        console.print(f"Extracted video_id: {video_id}")

        if video_id: 
            try:
                video_title = get_video_title(video_id)
            except Exception as title_e:
                console.print(f"[yellow]Warning: Could not retrieve video title for ID '{video_id}': {title_e}[/yellow]")
        else: 
             console.print(f"[red]Error: Could not extract video ID from URL: {video_url}[/red]")
             return {"video_title": video_title, "analysis": f"Error: Could not extract video ID from URL: {video_url}"}

        console.print(f"[green]Fetching transcript for video ID: {video_id} (Language: {language})...[/green]")
        
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        target_transcript_object = None
        try:
            target_transcript_object = transcript_list.find_transcript([language])
        except NoTranscriptFound:
            try:
                target_transcript_object = transcript_list.find_generated_transcript([language])
            except NoTranscriptFound:
                console.print(f"[red]🚫 Error: No transcript found for video ID {video_id} in language '{language}' or its fallbacks.[/red]")
                return {"video_title": video_title, "analysis": f"Error: Transcript not found for language '{language}'."}
        
        fetched_transcript_data = target_transcript_object.fetch()
        
        transcript_entries = [
            f"{format_time(entry['start'])}: {entry['text']}" 
            for entry in fetched_transcript_data
        ]
        transcript_text = "\n".join(transcript_entries)

    except TranscriptsDisabled:
        console.print(f"[red]🚫 Error: Transcripts are disabled for video ID: {video_id}[/red]")
        return {"video_title": video_title, "analysis": "Error: Transcripts disabled for this video."}
    except (NoTranscriptFound, CouldNotRetrieveTranscript) as specific_api_e:
        console.print(f"[red]🚫 Error: Could not retrieve transcript for video ID '{video_id}' (Language: {language}): {specific_api_e}[/red]")
        return {"video_title": video_title, "analysis": f"Error: Transcript not found or could not be retrieved (Language: {language})."}
    except Exception as e: 
        console.print(f"[red]🚫 Error during video processing or transcript fetching for '{video_url}': {e}[/red]")
        console.print("[red]Full stack trace:[/red]")
        traceback.print_exc() # Print the full stack trace
        return {"video_title": video_title, "analysis": f"Error: An unexpected error occurred while processing the video transcript. Details: {e}"}

    if not transcript_text:
        console.print("[yellow]Warning: Transcript text is empty. Analysis might be based on missing data.[/yellow]")
        # Allow proceeding, but prompt will indicate transcript unavailability

    prompt_text = f"""Analyze this YouTube video transcript and provide a structured breakdown:

*{video_title}*

*Introduction*
- Key objectives of the video
- Core themes and methodologies
- Target audience

*Detailed Analysis*
For each significant segment:
1. Time-stamped section header
2. 2-3 key verbatim excerpts
3. Technical analysis and implications

*Conclusion*
- Summary of key technical takeaways
- Practical applications
- Long-term recommendations

Formatting Rules:
- Use bullet points (•) for lists
- Avoid markdown formatting
- Never include URLs
- Keep excerpts under 20 words

[TRANSCRIPT]
{transcript_text if transcript_text else "Transcript not available."}
"""
    
    if prompt_only:
        return {"video_title": video_title, "prompt": prompt_text}
    
    console.print("[green]Generating AI analysis...[/green]")
    try:
        result = llm.invoke(prompt_text)
        analysis = result.content if hasattr(result, "content") else str(result)
    except Exception as llm_e:
        console.print(f"[red]🚫 Error during AI analysis generation: {llm_e}[/red]")
        console.print("[red]Full stack trace for LLM error:[/red]")
        traceback.print_exc() # Print stack trace for LLM errors too
        return {"video_title": video_title, "analysis": f"Error: Failed to generate AI analysis. Details: {llm_e}"}
    
    analysis = re.sub(r'\n{3,}', '\n\n', analysis) 
    analysis = re.sub(r'\*\*Video Analysis:\*\*', '', analysis) 
    
    return {"video_title": video_title, "analysis": analysis}

@tool
def generate_video_tags(analysis_text: str, llm: ChatOpenAI) -> str:
    """
    Generates YAML-formatted tags from analysis text.
    
    Args:
        analysis_text: Video analysis text
        llm: ChatOpenAI instance
        
    Returns:
        str: YAML tags list or error message
    """
    console = Console()
    prompt = f"""Extract key tags from this analysis. Return YAML list:

{analysis_text}

Format:
tags:
  - tag1
  - tag2
"""
    try:
        result = llm.invoke(prompt)
        content_str = result.content if hasattr(result, "content") else str(result)
        return content_str.replace("```yaml", "").replace("```", "").strip()
    except Exception as e:
        console.print(f"[red]🚫 Error during tag generation: {e}[/red]")
        console.print("[red]Full stack trace for tag generation error:[/red]")
        traceback.print_exc() # Print stack trace for tag generation errors
        return "tags:\n  - error_generating_tags"
