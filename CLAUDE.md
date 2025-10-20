# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of AI-powered CLI tools for document processing, GitHub PR analysis, YouTube content analysis, and structured Git workflows. The codebase follows a modular architecture with separate packages for different domains.

## Common Commands

### Main CLI Entry Point
```bash
# Unified CLI interface in ai_tools/
python ai_tools/main.py <command> [options]

# Available commands:
python ai_tools/main.py convert input.pdf --format enhanced --clipboard
python ai_tools/main.py github https://github.com/owner/repo/pull/123 --target slack --llm-provider anthropic

# YouTube - Single video (clipboard only)
python ai_tools/main.py youtube "https://youtu.be/VIDEO_ID" --dynamic-tags

# YouTube - Single video with file save (auto-uses markdown)
python ai_tools/main.py youtube "https://youtu.be/VIDEO_ID" --save-file --dynamic-tags

# YouTube - Multiple videos (batch processing - auto-uses markdown)
python ai_tools/main.py youtube "URL1" "URL2" "URL3" --save-file

# YouTube - Playlist (auto-extracts all videos, auto-uses markdown)
python ai_tools/main.py youtube "https://www.youtube.com/playlist?list=PLAYLIST_ID" --save-file
```

### Direct PR Review Tools
```bash
# MCP server for Claude Desktop integration
python mcp/pr_review_mcp_server.py

# Direct PR review with Claude integration
python mcp/claude_integrated_pr_review.py
```

### Structured Git Workflows (ngit)
```bash
# Kent Beck's "Tidy First?" approach
python ngit/main.py
```

### Setup and Dependencies
```bash
# Option 1: Docker (Recommended)
docker-compose up -d                                # Start API service
source scripts/docker-aliases.sh                   # Load Docker aliases

# Option 2: Local Development
pip install -r requirements.txt                    # Install dependencies

# Required environment variables
export ANTHROPIC_API_KEY="your_anthropic_key"      # For Claude LLM
export DEEPSEEK_API_KEY="your_deepseek_key"        # Alternative LLM provider
export GITHUB_TOKEN_WORK="your_github_token"       # GitHub API access
export YOUTUBE_API_KEY="your_youtube_key"          # YouTube Data API
export SLACK_TOKEN="your_slack_token"              # Slack integration
```

## Architecture Overview

### Core Modules

**ai_tools/** - Main unified CLI toolkit
- Entry point: `main.py` with subcommands (convert, github, youtube)
- Uses agent-based architecture with LangChain and SmolaAgents
- Supports multiple LLM providers (Anthropic Claude, DeepSeek)
- Rich console output with progress tracking

**api/** - FastAPI REST service
- `server.py` - Main FastAPI application with all endpoints
- Async processing with background tasks
- Pydantic models for request/response validation
- Full compatibility with existing CLI functionality

**pr_reviewer/** - Modular PR review package
- Object-oriented design with clear separation of concerns
- `reviewer.py` - Main orchestration
- `github_api.py` - GitHub API interactions
- `llm_analyzer.py` - AI analysis logic
- Security-focused reviews with performance analysis

**mcp/** - Model Context Protocol integration
- `claude_integrated_pr_review.py` - Direct Claude CLI integration
- `pr_review_mcp_server.py` - MCP server for Claude Desktop
- Enables natural language PR review commands

**ngit/** - Structured Git workflows
- Implements Kent Beck's "Tidy First?" philosophy
- Separates structural changes from behavioral changes
- AI-powered commit categorization with automatic backups

### Key Configuration Files

**llm_config.py** - Centralized LLM provider configuration
```python
def get_llm(provider: str = "anthropic"):
    # Supports both Anthropic Claude and DeepSeek
    # Environment variable based configuration
```

**requirements.txt** - Key dependencies include:
- LangChain, SmolaAgents for AI orchestration
- Rich, Questionary for enhanced CLI experience
- PyGithub, youtube-transcript-api for API integrations
- Docling for PDF processing
- FastAPI, Uvicorn for REST API service
- Pydantic for data validation

**Docker Configuration**
- `Dockerfile` - Container setup for API service
- `docker-compose.yml` - Service orchestration with environment variables
- `scripts/docker-aliases.sh` - Convenient Docker management aliases

## Development Patterns

### LLM Provider Abstraction
All tools support multiple LLM providers through centralized configuration. Use `--llm-provider` flag or modify `llm_config.py`.

### Rich CLI Interface
Tools use Rich library for enhanced console output with progress bars, panels, and markdown rendering. All output is designed for professional presentation.

### Safety and Backup
- All Git operations include automatic backup creation
- Dry-run modes available for testing
- Comprehensive error handling with graceful failures

### Multi-format Output
Tools generate output in multiple formats:
- GitHub Markdown for PR descriptions
- Slack formatting for team communication
- Clipboard integration for easy sharing

## Working with Different Tool Categories

### PDF Processing
- Main utility: `ai_tools/main.py convert`
- Standalone scripts: `read_page_in_pdf.py`, `search_in_pdf.py`, `copy_pdf_content.py`
- Supports local files and URLs with enhanced formatting options

### GitHub PR Analysis
- Primary: `ai_tools/main.py github` or `pr_reviewer/` package
- Features: Diff analysis, security review, performance insights
- Can automatically update PR descriptions

### YouTube Content Analysis
- Command: `ai_tools/main.py youtube`
- Features: Transcript extraction, content breakdown, dynamic tag generation
- Multi-language support with chronological analysis
- **NEW**: Batch processing for multiple videos or playlists
- **NEW**: Automatic markdown file generation with sanitized filenames
- **NEW**: Progress tracking for batch operations

### Structured Git Operations
- Tool: `ngit/main.py`
- Philosophy: Separate structural from behavioral changes
- AI categorization of commits with semantic classification

## Integration Points

The repository is designed for both standalone tool usage and integration into larger AI-powered workflows. Key integration patterns:

- **REST API Service**: FastAPI endpoints for multi-user access and system integration
- **Docker Containerization**: Easy deployment across different environments
- **MCP Integration**: Direct Claude Desktop integration via MCP server
- **API Integration**: GitHub, YouTube, Slack APIs with proper authentication
- **Multi-Provider LLM**: Seamless switching between Anthropic and DeepSeek
- **Cross-Tool Workflow**: Tools can be chained together for complex document processing pipelines

### API Endpoints
- `POST /api/v1/convert/pdf` - PDF to Markdown conversion
- `POST /api/v1/github/analyze-pr` - GitHub PR analysis
- `POST /api/v1/youtube/analyze` - YouTube content analysis
- `GET /health` - Service health check

### Docker Usage
```bash
# Start API service
docker-compose up -d

# Use CLI client that talks to API
python scripts/api_client.py convert document.pdf --format enhanced

# Check service health
curl http://localhost:8000/health
```