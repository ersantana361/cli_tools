# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of AI-powered CLI tools for document processing, GitHub PR analysis, YouTube content analysis, and structured Git workflows. The codebase follows a modular architecture with separate packages for different domains.

## Common Commands

### Main CLI Entry Point
```bash
# Using the 'ai' alias (recommended - see Docker Usage section)
ai <command> [options]

# Or directly with docker-run.sh
./docker-run.sh <command> [options]

# Available commands:
ai convert input.pdf --format enhanced --clipboard
ai github https://github.com/owner/repo/pull/123 --target slack --llm-provider anthropic

# YouTube - Single video analysis
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --dynamic-tags

# YouTube - With specific LLM provider
ai youtube "https://youtu.be/VIDEO_ID" --save-file --llm-provider deepseek

# YouTube - Process entire playlist (simplified interface)
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --output-dir ./summaries

# YouTube - Preview playlist videos without processing
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --dry-run
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
- Entry point: `main.py` with subcommands (convert, github, youtube, process-playlist)
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
- Commands: `ai youtube` (single/batch) and `ai process-playlist` (playlists)
- Features: Transcript extraction, content breakdown, dynamic tag generation
- Multi-language support with chronological analysis
- Batch processing stops on first failure (fail-fast)
- Automatic markdown file generation with sanitized filenames
- Progress tracking for batch operations

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

This repository supports full Docker containerization for both API services and CLI tools.

#### Quick Start
```bash
# Build the Docker image
docker-compose build

# Set up the 'ai' alias (add to ~/.bashrc or ~/.zshrc for persistence)
alias ai='./docker-run.sh'

# Or with absolute path for use from any directory
alias ai='/path/to/cli_tools/docker-run.sh'
```

#### Using the `ai` Command

Once the alias is set, run any command with `ai <subcommand>`:

```bash
# YouTube - Single video analysis
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --dynamic-tags

# YouTube - With specific LLM provider
ai youtube "https://youtu.be/VIDEO_ID" --save-file --llm-provider deepseek

# YouTube - Process entire playlist
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --output-dir ./summaries

# YouTube - Dry run to preview playlist videos
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --dry-run

# PDF conversion
ai convert input.pdf --format enhanced --clipboard

# GitHub PR analysis
ai github https://github.com/owner/repo/pull/123 --target slack
```

#### Available Commands

| Command | Description |
|---------|-------------|
| `ai youtube` | Analyze single/multiple YouTube videos |
| `ai process-playlist` | Process all videos in a YouTube playlist |
| `ai convert` | Convert PDF to Markdown |
| `ai github` | Analyze GitHub PRs |

#### Running Without Alias

If you prefer not to use an alias:
```bash
./docker-run.sh youtube "https://youtu.be/VIDEO_ID" --save-file
./docker-run.sh process-playlist "PLAYLIST_URL" --output-dir ./summaries
./docker-run.sh convert input.pdf --format enhanced
./docker-run.sh github https://github.com/owner/repo/pull/123
```

#### Alternative: Docker Aliases Script
```bash
# Load additional Docker management aliases
source scripts/docker-aliases.sh

# API management
ai_api_start      # Start API service
ai_api_stop       # Stop API service
ai_api_logs       # View logs
ai_api_health     # Check health
ai_api_restart    # Restart service
ai_docker_rebuild # Rebuild from scratch
ai_docker_shell   # Get shell access
ai_docker_clean   # Clean up resources
```

#### Environment Variables
Docker containers automatically use environment variables from your shell:
```bash
export ANTHROPIC_API_KEY="your_key"
export DEEPSEEK_API_KEY="your_key"
export GITHUB_TOKEN_WORK="your_token"
export YOUTUBE_API_KEY="your_key"
export SLACK_TOKEN="your_token"
```

#### Volume Mounts
The Docker setup includes these volume mounts:
- `./workspace:/workspace` - For input/output files
- `~/.claude:/home/appuser/.claude:ro` - Claude configuration (read-only)
- `.:/app` - Live code updates during development
- `/tmp/.X11-unix` - X11 socket for clipboard support

#### Troubleshooting
```bash
# View all available Docker commands
ai_docker_help

# Check API health
curl http://localhost:8000/health

# View container logs
docker-compose logs -f ai-tools-api

# Rebuild if dependencies changed
docker-compose build --no-cache
```