from rich.console import Console
import re
import traceback
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from langchain_openai import ChatOpenAI
from smolagents import tool
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
        
        # Smart transcript selection with multiple fallback strategies
        target_transcript_object = None
        selected_language = None
        
        # Strategy 1: Try requested language (manual first, then generated)
        try:
            target_transcript_object = transcript_list.find_transcript([language])
            selected_language = language
            console.print(f"[green]Found manual transcript for {language}[/green]")
        except NoTranscriptFound:
            try:
                target_transcript_object = transcript_list.find_generated_transcript([language])
                selected_language = language
                console.print(f"[green]Found generated transcript for {language}[/green]")
            except NoTranscriptFound:
                console.print(f"[yellow]No transcript found for {language}, trying fallbacks...[/yellow]")
        
        # Strategy 2: If requested language fails and isn't English, try English
        if target_transcript_object is None and language != 'en':
            try:
                target_transcript_object = transcript_list.find_transcript(['en'])
                selected_language = 'en'
                console.print("[green]Found manual English transcript as fallback[/green]")
            except NoTranscriptFound:
                try:
                    target_transcript_object = transcript_list.find_generated_transcript(['en'])
                    selected_language = 'en'
                    console.print("[green]Found generated English transcript as fallback[/green]")
                except NoTranscriptFound:
                    console.print("[yellow]No English transcript found either...[/yellow]")
        
        # Strategy 3: Use any available transcript as last resort
        if target_transcript_object is None:
            try:
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    target_transcript_object = available_transcripts[0]
                    selected_language = target_transcript_object.language_code
                    console.print(f"[yellow]Using any available transcript: {selected_language}[/yellow]")
                else:
                    console.print(f"[red]🚫 Error: No transcripts available for video ID {video_id}[/red]")
                    return {"video_title": video_title, "analysis": "Error: No transcripts available for this video."}
            except Exception as list_e:
                console.print(f"[red]🚫 Error listing transcripts: {list_e}[/red]")
                return {"video_title": video_title, "analysis": f"Error: Could not list available transcripts. Details: {list_e}"}
        
        # Fetch transcript data with multiple retry strategies
        fetched_transcript_data = None
        for attempt in range(3):  # Try up to 3 times
            try:
                console.print(f"[green]Fetching transcript data (attempt {attempt + 1}/3)...[/green]")
                fetched_transcript_data = target_transcript_object.fetch()
                break  # Success, exit retry loop
            except Exception as fetch_e:
                console.print(f"[yellow]Attempt {attempt + 1} failed: {fetch_e}[/yellow]")
                if attempt == 2:  # Last attempt
                    console.print(f"[red]🚫 All transcript fetch attempts failed for {selected_language}[/red]")
                    # Try one more fallback - get any other available transcript
                    try:
                        available_transcripts = list(transcript_list)
                        for alt_transcript in available_transcripts:
                            if alt_transcript.language_code != selected_language:
                                console.print(f"[yellow]Trying alternative transcript: {alt_transcript.language_code}[/yellow]")
                                try:
                                    fetched_transcript_data = alt_transcript.fetch()
                                    selected_language = alt_transcript.language_code
                                    console.print(f"[green]Successfully fetched {selected_language} transcript![/green]")
                                    break
                                except Exception:
                                    continue
                        if fetched_transcript_data is None:
                            return {"video_title": video_title, "analysis": f"Error: Could not fetch any transcript. XML parsing consistently fails. Details: {fetch_e}"}
                    except Exception as final_e:
                        return {"video_title": video_title, "analysis": f"Error: All transcript retrieval strategies failed. Details: {final_e}"}
                else:
                    import time
                    time.sleep(1)  # Brief delay before retry
        
        if fetched_transcript_data:
            transcript_entries = [
                f"{format_time(entry['start'])}: {entry['text']}" 
                for entry in fetched_transcript_data
            ]
            transcript_text = "\n".join(transcript_entries)
            console.print(f"[green]Successfully processed {len(transcript_entries)} transcript entries in {selected_language}[/green]")
        else:
            transcript_text = ""
            console.print("[yellow]No transcript data available[/yellow]")

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
        
        # Try one more fallback - manual transcript retrieval without language preference
        try:
            console.print("[yellow]Attempting final fallback - any available transcript...[/yellow]")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = list(transcript_list)
            if available_transcripts:
                any_transcript = available_transcripts[0]
                console.print(f"[yellow]Using any available transcript: {any_transcript.language_code}[/yellow]")
                fetched_transcript_data = any_transcript.fetch()
                transcript_entries = [
                    f"{format_time(entry['start'])}: {entry['text']}" 
                    for entry in fetched_transcript_data
                ]
                transcript_text = "\n".join(transcript_entries)
                console.print(f"[green]Successfully retrieved fallback transcript ({len(transcript_entries)} entries)[/green]")
            else:
                return {"video_title": video_title, "analysis": f"Error: No transcripts available for this video. Details: {e}"}
        except Exception as final_e:
            console.print(f"[red]Final fallback also failed: {final_e}[/red]")
            return {"video_title": video_title, "analysis": f"Error: All transcript retrieval methods failed. Details: {e}"}

    if not transcript_text:
        console.print("[yellow]Warning: Transcript text is empty. Analysis might be based on missing data.[/yellow]")
        # Check if we got here via fallback and have some data
        if 'transcript_entries' in locals() and transcript_entries:
            transcript_text = "\n".join(transcript_entries)
        # Allow proceeding, but prompt will indicate transcript unavailability

    prompt_text = f"""Analyze this YouTube video transcript and provide a structured breakdown:

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

Formatting Rules for {"Slack" if target == "slack" else "Markdown"}:
- Use bullet points (•) for lists
- Use *bold* for headers and emphasis
- Never include URLs or video title in output
- Keep excerpts under 20 words
- Clean, professional formatting

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
