from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
import asyncio
from datetime import datetime
import tempfile
import os
import sys

# Add parent directory to path to import tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_tools.tools.pdf_converter import run_conversion
from ai_tools.tools.github_agent import run_github
from ai_tools.tools.youtube_agent import run_youtube
from rich.console import Console

app = FastAPI(
    title="AI Tools API",
    description="API for PDF conversion, GitHub PR analysis, and YouTube content analysis",
    version="1.0.0"
)

# Pydantic models for request/response
class PDFConvertRequest(BaseModel):
    input_source: str
    format: Literal["basic", "enhanced"] = "basic"
    verbose: bool = False

class PDFConvertResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None

class GitHubAnalyzeRequest(BaseModel):
    pr_link: HttpUrl
    target: Literal["github", "slack"] = "github"
    llm_provider: Literal["anthropic", "deepseek"] = "anthropic"

class GitHubAnalyzeResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    error: Optional[str] = None

class YouTubeAnalyzeRequest(BaseModel):
    video: Optional[str] = None
    language: str = "en"
    target: Literal["markdown", "slack"] = "markdown"
    slack_thread: Optional[str] = None
    slack_channel: Optional[str] = None
    prompt_only: bool = False
    dynamic_tags: bool = False
    llm_provider: Literal["anthropic", "deepseek"] = "anthropic"

class YouTubeAnalyzeResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/api/v1/convert/pdf", response_model=PDFConvertResponse)
async def convert_pdf(request: PDFConvertRequest):
    try:
        console = Console(file=open(os.devnull, 'w'))  # Suppress console output
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as temp_file:
            temp_output = temp_file.name
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                run_conversion,
                request.input_source,
                temp_output,
                request.verbose,
                request.format,
                False,  # clipboard
                console
            )
            
            with open(temp_output, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return PDFConvertResponse(success=True, content=content)
        
        finally:
            if os.path.exists(temp_output):
                os.unlink(temp_output)
    
    except Exception as e:
        return PDFConvertResponse(success=False, error=str(e))

@app.post("/api/v1/github/analyze-pr", response_model=GitHubAnalyzeResponse)
async def analyze_github_pr(request: GitHubAnalyzeRequest):
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_github,
            str(request.pr_link),
            request.target,
            request.llm_provider
        )
        
        return GitHubAnalyzeResponse(success=True, analysis=str(result))
    
    except Exception as e:
        return GitHubAnalyzeResponse(success=False, error=str(e))

@app.post("/api/v1/youtube/analyze", response_model=YouTubeAnalyzeResponse)
async def analyze_youtube(request: YouTubeAnalyzeRequest):
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_youtube,
            request.video,
            request.language,
            request.target,
            request.prompt_only,
            request.dynamic_tags,
            request.slack_thread,
            request.slack_channel,
            False,  # ask_for_url
            request.llm_provider
        )
        
        return YouTubeAnalyzeResponse(success=True, analysis=str(result))
    
    except Exception as e:
        return YouTubeAnalyzeResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)