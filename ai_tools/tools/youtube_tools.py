from rich.console import Console
import re
import traceback
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from langchain_openai import ChatOpenAI
from smolagents import tool
from tools.youtube_utils import extract_video_id, get_video_title, format_time

@tool
def fetch_youtube_transcript(video_url: str, language: str = "en") -> dict:
    """
    Standalone function to fetch YouTube transcript for debugging purposes.
    
    Args:
        video_url: YouTube video URL or ID
        language: Language code (e.g. "en")
        
    Returns:
        dict: Contains transcript_text, video_title, selected_language, and status info
    """
    console = Console()
    result = {
        "video_url": video_url,
        "requested_language": language,
        "video_title": "Unknown Title",
        "transcript_text": "",
        "selected_language": None,
        "status": "failed",
        "error": None,
        "attempts": []
    }
    
    try:
        console.print(f"[cyan]🔍 Fetching transcript for: {video_url}[/cyan]")
        
        # Extract video ID
        video_id = extract_video_id(video_url)
        console.print(f"[green]✅ Extracted video ID: {video_id}[/green]")
        
        if not video_id:
            result["error"] = "Could not extract video ID from URL"
            return result
            
        # Get video title
        try:
            video_title = get_video_title(video_id)
            result["video_title"] = video_title
            console.print(f"[green]✅ Video title: {video_title}[/green]")
        except Exception as title_e:
            console.print(f"[yellow]⚠️ Could not get title: {title_e}[/yellow]")
            
        # List available transcripts
        console.print(f"[cyan]🔍 Listing available transcripts...[/cyan]")
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # Show all available transcripts
        available_transcripts = list(transcript_list)
        console.print(f"[green]✅ Found {len(available_transcripts)} transcript(s):[/green]")
        
        for i, transcript in enumerate(available_transcripts):
            is_generated = transcript.is_generated
            console.print(f"  {i+1}. {transcript.language} ({transcript.language_code}) - {'Generated' if is_generated else 'Manual'}")
            result["attempts"].append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": is_generated,
                "available": True
            })
            
        # Strategy 1: Try requested language (manual first, then generated)
        console.print(f"\n[cyan]🎯 Trying requested language: {language}[/cyan]")
        target_transcript = None
        
        try:
            target_transcript = transcript_list.find_transcript([language])
            result["selected_language"] = language
            console.print(f"[green]✅ Found manual transcript for {language}[/green]")
        except NoTranscriptFound:
            console.print(f"[yellow]⚠️ No manual transcript for {language}[/yellow]")
            try:
                target_transcript = transcript_list.find_generated_transcript([language])
                result["selected_language"] = language
                console.print(f"[green]✅ Found generated transcript for {language}[/green]")
            except NoTranscriptFound:
                console.print(f"[red]❌ No transcript found for {language}[/red]")
        
        # Strategy 2: Try English if not already tried
        if target_transcript is None and language != 'en':
            console.print(f"\n[cyan]🎯 Trying English fallback...[/cyan]")
            try:
                target_transcript = transcript_list.find_transcript(['en'])
                result["selected_language"] = 'en'
                console.print("[green]✅ Found manual English transcript[/green]")
            except NoTranscriptFound:
                try:
                    target_transcript = transcript_list.find_generated_transcript(['en'])
                    result["selected_language"] = 'en'
                    console.print("[green]✅ Found generated English transcript[/green]")
                except NoTranscriptFound:
                    console.print("[red]❌ No English transcript found[/red]")
        
        # Strategy 3: Use first available transcript
        if target_transcript is None and available_transcripts:
            console.print(f"\n[cyan]🎯 Trying first available transcript...[/cyan]")
            target_transcript = available_transcripts[0]
            result["selected_language"] = target_transcript.language_code
            console.print(f"[yellow]⚠️ Using any available: {target_transcript.language_code}[/yellow]")
        
        if target_transcript is None:
            result["error"] = "No transcripts available for this video"
            console.print("[red]❌ No transcripts available[/red]")
            return result
            
        # Fetch transcript data
        console.print(f"\n[cyan]📥 Fetching transcript data for {result['selected_language']}...[/cyan]")
        
        for attempt in range(3):
            try:
                console.print(f"[dim]Attempt {attempt + 1}/3...[/dim]")
                transcript_data = target_transcript.fetch()
                
                # Format transcript
                transcript_entries = [
                    f"{format_time(entry['start'])}: {entry['text']}" 
                    for entry in transcript_data
                ]
                result["transcript_text"] = "\n".join(transcript_entries)
                result["status"] = "success"
                
                console.print(f"[green]✅ Successfully fetched {len(transcript_entries)} entries![/green]")
                console.print(f"[dim]Total characters: {len(result['transcript_text'])}[/dim]")
                console.print(f"[dim]First entry: {transcript_entries[0] if transcript_entries else 'None'}[/dim]")
                
                return result
                
            except Exception as fetch_e:
                console.print(f"[red]❌ Attempt {attempt + 1} failed: {fetch_e}[/red]")
                result["attempts"].append({
                    "attempt": attempt + 1,
                    "error": str(fetch_e),
                    "language_code": result['selected_language']
                })
                
                if attempt == 2:  # Last attempt
                    result["error"] = f"All fetch attempts failed: {fetch_e}"
                    console.print(f"[red]🚫 All attempts failed for {result['selected_language']}[/red]")
                else:
                    import time
                    time.sleep(1)  # Brief delay before retry
        
    except TranscriptsDisabled:
        error_msg = "Transcripts are disabled for this video"
        result["error"] = error_msg
        console.print(f"[red]🚫 {error_msg}[/red]")
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        result["error"] = error_msg
        console.print(f"[red]🚫 {error_msg}[/red]")
        import traceback
        console.print("[red]Full traceback:[/red]")
        traceback.print_exc()
    
    return result

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

        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
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
                            # Interactive prompt for handling no transcript
                            from rich.prompt import Confirm, Prompt
                            from rich.panel import Panel
                            
                            # Make sure any progress indicators are stopped
                            console.print()  # New line to clear any spinners
                            import sys
                            sys.stdout.flush()  # Flush output buffer
                            console.print(Panel.fit(
                                "[yellow]⚠️ No Transcript Available[/yellow]\n\n"
                                "This video doesn't have usable captions/transcripts.\n"
                                "You can either:\n"
                                "• Continue with video title and URL only\n"
                                "• Provide a manual transcript/summary",
                                title="[bold yellow]Transcript Issue[/bold yellow]",
                                border_style="yellow"
                            ))
                            
                            # Create a fresh console instance for prompts
                            from rich.console import Console as FreshConsole
                            prompt_console = FreshConsole()
                            
                            use_manual = Confirm.ask(
                                "[bold cyan]Would you like to provide a manual transcript or summary?[/bold cyan]",
                                console=prompt_console,
                                default=False
                            )
                            
                            if use_manual:
                                prompt_console.print("\n[cyan]💡 You can paste the video description, your notes, or a brief summary[/cyan]")
                                manual_text = Prompt.ask(
                                    "[bold cyan]Please paste your transcript/summary[/bold cyan]",
                                    console=prompt_console,
                                    default=""
                                )
                                if manual_text.strip():
                                    transcript_text = manual_text.strip()
                                    console.print(Panel.fit(
                                        f"✅ Using manual input ({len(transcript_text)} characters)",
                                        border_style="green"
                                    ))
                                else:
                                    transcript_text = f"Video: {video_title}\nURL: {video_url}\nNote: No transcript available"
                            else:
                                console.print("[dim]User declined manual input - exiting[/dim]")
                                return {"video_title": video_title, "analysis": "Error: No transcript available and user declined manual input."}
                    except Exception as final_e:
                        return {"video_title": video_title, "analysis": f"Error: All transcript retrieval strategies failed. Details: {final_e}"}
                else:
                    import time
                    time.sleep(1)  # Brief delay before retry
        
        if fetched_transcript_data:
            transcript_entries = [
                f"{format_time(entry.start)}: {entry.text}" 
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
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            available_transcripts = list(transcript_list)
            if available_transcripts:
                any_transcript = available_transcripts[0]
                console.print(f"[yellow]Using any available transcript: {any_transcript.language_code}[/yellow]")
                fetched_transcript_data = any_transcript.fetch()
                transcript_entries = [
                    f"{format_time(entry.start)}: {entry.text}" 
                    for entry in fetched_transcript_data
                ]
                transcript_text = "\n".join(transcript_entries)
                console.print(f"[green]Successfully retrieved fallback transcript ({len(transcript_entries)} entries)[/green]")
            else:
                # Interactive prompt for no transcripts available
                from rich.prompt import Confirm, Prompt
                from rich.panel import Panel
                
                # Make sure any progress indicators are stopped
                console.print()  # New line to clear any spinners
                import sys
                sys.stdout.flush()  # Flush output buffer
                console.print(Panel.fit(
                    "[yellow]⚠️ No Transcript Available[/yellow]\n\n"
                    "This video doesn't have any captions/transcripts.\n"
                    "You can either:\n"
                    "• Continue with video title and URL only\n"
                    "• Provide a manual transcript/summary",
                    title="[bold yellow]Transcript Issue[/bold yellow]",
                    border_style="yellow"
                ))
                
                # Create a fresh console instance for prompts
                from rich.console import Console as FreshConsole
                prompt_console = FreshConsole()
                
                use_manual = Confirm.ask(
                    "[bold cyan]Would you like to provide a manual transcript or summary?[/bold cyan]",
                    console=prompt_console,
                    default=False
                )
                
                if use_manual:
                    prompt_console.print("\n[cyan]💡 You can paste the video description, your notes, or a brief summary[/cyan]")
                    manual_text = Prompt.ask(
                        "[bold cyan]Please paste your transcript/summary[/bold cyan]",
                        console=prompt_console,
                        default=""
                    )
                    if manual_text.strip():
                        transcript_text = manual_text.strip()
                        console.print(Panel.fit(
                            f"✅ Using manual input ({len(transcript_text)} characters)",
                            border_style="green"
                        ))
                    else:
                        transcript_text = f"Video: {video_title}\nURL: {video_url}\nNote: No transcript available"
                else:
                    console.print("[dim]User declined manual input - exiting[/dim]")
                    return {"video_title": video_title, "analysis": "Error: No transcript available and user declined manual input."}
        except Exception as final_e:
            console.print(f"[red]Final fallback also failed: {final_e}[/red]")
            # Interactive prompt as last resort
            from rich.prompt import Confirm, Prompt
            from rich.panel import Panel
            
            # Make sure any progress indicators are stopped
            console.print()  # New line to clear any spinners
            import sys
            sys.stdout.flush()  # Flush output buffer
            console.print(Panel.fit(
                "[red]🚫 Transcript Fetch Failed[/red]\n\n"
                f"All transcript retrieval methods failed.\n"
                f"Error: {e}\n\n"
                "You can still continue by providing manual content.",
                title="[bold red]Error[/bold red]",
                border_style="red"
            ))
            
            # Create a fresh console instance for prompts
            from rich.console import Console as FreshConsole
            prompt_console = FreshConsole()
            
            use_manual = Confirm.ask(
                "[bold cyan]Would you like to provide manual content instead?[/bold cyan]",
                console=prompt_console,
                default=False
            )
            
            if use_manual:
                manual_text = Prompt.ask(
                    "[bold cyan]Please paste your transcript/summary[/bold cyan]",
                    console=prompt_console,
                    default=""
                )
                if manual_text.strip():
                    transcript_text = manual_text.strip()
                else:
                    transcript_text = f"Video: {video_title}\nURL: {video_url}\nNote: Transcript fetch failed"
            else:
                console.print("[dim]User declined manual input - exiting[/dim]")
                return {"video_title": video_title, "analysis": "Error: No transcript available and user declined manual input."}

    if not transcript_text:
        console.print("[red]🚫 No transcript data available - cannot proceed with analysis[/red]")
        return {"video_title": video_title, "analysis": "Error: No transcript data available for analysis."}

    # Adjust prompt based on available content
    has_actual_transcript = transcript_text and not transcript_text.startswith("Video:") and "No transcript available" not in transcript_text
    
    if has_actual_transcript:
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
{transcript_text}
"""
    else:
        prompt_text = f"""Analyze this YouTube video based on available information:

Video Title: {video_title}

Since no transcript is available, provide a structured response based on the title and any provided context:

*Video Overview*
- Likely objectives based on the title
- Potential target audience
- Expected content themes

*Analysis Approach*
- What viewers might learn from this video
- Key topics likely covered
- Relevant technical areas

*Recommendations*
- How to get the most value from this video
- Related topics to explore
- Next steps for learning

Note: Analysis is based on title only since transcript is unavailable.

[AVAILABLE CONTENT]
{transcript_text if transcript_text else f"Video Title: {video_title}"}
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
