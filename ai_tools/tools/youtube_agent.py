import os
import pyperclip
import traceback
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from langchain_openai import ChatOpenAI
from tools.youtube_tools import analyze_video, generate_video_tags

def run_youtube(video: str, language: str, target: str, prompt_only: bool, dynamic_tags: bool):
    console = Console()
    try:
        console.print("🚀 Starting YouTube video analysis process...\n")
        # Initialize the ChatOpenAI instance.
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        if not DEEPSEEK_API_KEY:
            raise Exception("Missing DEEPSEEK_API_KEY environment variable")
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat",
            base_url="https://api.deepseek.com"
        )
        
        # Run the analysis tool.
        analysis_result = analyze_video(
            video_url=video,
            language=language,
            target=target,
            prompt_only=prompt_only,
            llm=llm
        )
        video_title = analysis_result.get("video_title", "Untitled Video")
        output_body = analysis_result.get("prompt") if prompt_only else analysis_result.get("analysis")
        
        # Optionally generate dynamic tags.
        if target.lower() == "markdown" and (not prompt_only) and dynamic_tags:
            tags = generate_video_tags(analysis_text=output_body, llm=llm)
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
{tags}
---
"""
        else:
            metadata = f"""---
title: {video_title} Video Analysis Report
draft: false
tags:
  - youtube
  - video analysis
  - transcript
  - smolagents
---
"""
        
        final_output = metadata + "\n" + output_body if target.lower() == "markdown" else output_body
        
        # Copy output to clipboard and display it.
        pyperclip.copy(final_output)
        console.print(Panel(f"Video Title: {video_title}", title="Video Analysis", expand=False))
        console.print(Markdown("=== Video Analysis Output ==="))
        console.print(Markdown(final_output))
    except Exception as e:
        console.print(f"🚫 Error: {e}")
        traceback.print_exc()
