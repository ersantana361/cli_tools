# Docker Setup Guide

This guide covers running AI Tools in a fully dockerized environment.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Environment variables configured (see below)

## Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd cli_tools

# 2. Set up environment variables
export ANTHROPIC_API_KEY="your_anthropic_key"
export DEEPSEEK_API_KEY="your_deepseek_key"
export GITHUB_TOKEN_WORK="your_github_token"
export YOUTUBE_API_KEY="your_youtube_key"
export SLACK_TOKEN="your_slack_token"

# 3. Build Docker image
docker-compose build

# 4. Load Docker aliases
source scripts/docker-aliases.sh

# 5. Start using the tools!
ai_docker_help  # See all available commands
```

## Running CLI Tools

### Using Docker Aliases (Recommended)

After loading aliases with `source scripts/docker-aliases.sh`, you can use these commands:

```bash
# PDF/Document Conversion
ai_convert_docker document.pdf --format enhanced --clipboard
ai_convert_docker https://example.com/document.pdf --format simple

# GitHub PR Analysis
ai_github_docker https://github.com/owner/repo/pull/123
ai_github_docker https://github.com/owner/repo/pull/123 --target slack --llm-provider anthropic

# YouTube Analysis
ai_youtube_docker "https://youtu.be/VIDEO_ID" --save-file --dynamic-tags
ai_youtube_docker "URL1" "URL2" "URL3" --save-file  # Batch processing
ai_youtube_docker "https://www.youtube.com/playlist?list=PLAYLIST_ID" --save-file  # Playlist

# Structured Git Workflow
ngit_docker

# PR Review
pr_review_docker --pr-url https://github.com/owner/repo/pull/123
```

### Using docker-run.sh Wrapper

```bash
./docker-run.sh python ai_tools/main.py convert input.pdf --format enhanced
./docker-run.sh python ai_tools/main.py github <PR_URL>
./docker-run.sh python ai_tools/main.py youtube <VIDEO_URL> --save-file
./docker-run.sh python ngit/main.py
```

## Running the API Service

```bash
# Start API service
ai_api_start

# Check health
ai_api_health

# View logs
ai_api_logs

# Stop service
ai_api_stop

# Restart service
ai_api_restart
```

### Using the API

Once the API is running, you can make HTTP requests:

```bash
# Health check
curl http://localhost:8000/health

# PDF conversion
curl -X POST http://localhost:8000/api/v1/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/workspace/document.pdf", "format": "enhanced"}'

# GitHub PR analysis
curl -X POST http://localhost:8000/api/v1/github/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://github.com/owner/repo/pull/123"}'

# YouTube analysis
curl -X POST http://localhost:8000/api/v1/youtube/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/VIDEO_ID"}'
```

## Environment Variables

The following environment variables are required:

| Variable | Description | Required For |
|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Claude LLM |
| `DEEPSEEK_API_KEY` | DeepSeek API key | DeepSeek LLM |
| `GITHUB_TOKEN_WORK` | GitHub personal access token | PR analysis |
| `YOUTUBE_API_KEY` | YouTube Data API key | YouTube analysis |
| `SLACK_TOKEN` | Slack bot token | Slack formatting |

Set them in your shell before running Docker commands:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN_WORK="ghp_..."
# etc.
```

Or create a `.env` file (not committed to git):

```bash
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
GITHUB_TOKEN_WORK=ghp_...
YOUTUBE_API_KEY=...
SLACK_TOKEN=xoxb-...
```

Then load it:
```bash
export $(cat .env | xargs)
```

## Volume Mounts

The Docker setup includes these volume mounts:

- `./workspace:/workspace` - Put your input files here, outputs are saved here
- `~/.claude:/home/appuser/.claude:ro` - Claude CLI configuration (read-only)
- `.:/app` - Live code mounting for development
- `/tmp/.X11-unix:/tmp/.X11-unix:ro` - X11 socket for clipboard support

## File Paths

When running in Docker, use these paths:

```bash
# For files in the workspace directory
ai_convert_docker /workspace/document.pdf

# For files in the current directory (mounted to /app)
ai_convert_docker /app/document.pdf

# URLs work normally
ai_convert_docker https://example.com/document.pdf
```

## Development Workflow

```bash
# 1. Make code changes in your editor

# 2. Rebuild if dependencies changed
docker-compose build

# 3. Test your changes
ai_convert_docker /workspace/test.pdf

# 4. Get shell access for debugging
ai_docker_shell

# Inside the container:
python ai_tools/main.py convert /workspace/test.pdf
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs ai-tools-api

# Rebuild from scratch
ai_docker_rebuild
```

### Environment variables not working
```bash
# Verify they're set
echo $ANTHROPIC_API_KEY

# Check inside container
docker run --rm -it cli_tools-ai-tools-api env | grep ANTHROPIC
```

### Permission errors
```bash
# The container runs as user 'appuser'
# Make sure your workspace directory is readable
chmod -R 755 workspace/
```

### Clipboard not working
```bash
# Make sure X11 socket is accessible
xhost +local:docker  # On Linux

# Or use --save-file instead of --clipboard
ai_youtube_docker "VIDEO_URL" --save-file
```

## Utility Commands

```bash
# View all Docker commands
ai_docker_help

# Rebuild images
ai_docker_rebuild

# Get shell access
ai_docker_shell

# Clean up resources
ai_docker_clean

# View running containers
docker ps

# View all containers
docker ps -a

# View images
docker images
```

## Architecture

The Docker setup includes two services:

1. **ai-tools-api** - FastAPI server for REST API access
   - Runs on port 8000
   - Auto-starts with `docker-compose up -d`
   - Health check endpoint at `/health`

2. **ai-tools-cli** - CLI command execution
   - Profile-based (only starts when needed)
   - Used by `docker-run.sh` wrapper
   - Ephemeral containers that stop after command execution

## Best Practices

1. **Use aliases** - They're more convenient and handle paths automatically
2. **Keep files in workspace/** - Easier to manage input/output
3. **Set environment variables once** - Add to your `.bashrc` or `.zshrc`
4. **Use --save-file** - More reliable than clipboard in Docker
5. **Monitor API logs** - Use `ai_api_logs` to debug issues

## Examples

### Complete Workflow Example

```bash
# Start fresh
cd cli_tools
source scripts/docker-aliases.sh
ai_api_start

# Convert a PDF
curl -o workspace/sample.pdf "https://example.com/document.pdf"
ai_convert_docker /workspace/sample.pdf --format enhanced > workspace/output.md

# Analyze a PR
ai_github_docker https://github.com/nodejs/node/pull/12345 --target github

# Analyze YouTube playlist
ai_youtube_docker "https://www.youtube.com/playlist?list=PLExample" --save-file

# Check results
ls -la workspace/

# Stop when done
ai_api_stop
```

## Additional Resources

- [CLAUDE.md](./CLAUDE.md) - Full project documentation
- [README.md](./README.md) - Project overview
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
