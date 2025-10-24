#!/bin/bash
# Docker aliases for AI Tools - API and CLI commands

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

# =============================================================================
# API Service Management
# =============================================================================

# Start the API service
alias ai_api_start='docker-compose up -d ai-tools-api'

# Stop the API service
alias ai_api_stop='docker-compose down'

# View API logs
alias ai_api_logs='docker-compose logs -f ai-tools-api'

# Restart API service
alias ai_api_restart='docker-compose restart ai-tools-api'

# Build and start API
alias ai_api_build='docker-compose build && docker-compose up -d ai-tools-api'

# Check API health
alias ai_api_health='curl -s http://localhost:8000/health | jq'

# =============================================================================
# CLI Commands in Docker
# =============================================================================

# Main CLI tool wrapper
alias ai_tools_docker="$SCRIPT_DIR/docker-run.sh python ai_tools/main.py"

# PDF/Document conversion
alias ai_convert_docker="$SCRIPT_DIR/docker-run.sh python ai_tools/main.py convert"

# GitHub PR analysis
alias ai_github_docker="$SCRIPT_DIR/docker-run.sh python ai_tools/main.py github"

# YouTube content analysis
alias ai_youtube_docker="$SCRIPT_DIR/docker-run.sh python ai_tools/main.py youtube"

# Structured git workflow
alias ngit_docker="$SCRIPT_DIR/docker-run.sh python ngit/main.py"

# PR reviewer (direct)
alias pr_review_docker="$SCRIPT_DIR/docker-run.sh python pr_reviewer/reviewer.py"

# =============================================================================
# Utility Functions
# =============================================================================

# Rebuild Docker images
alias ai_docker_rebuild='docker-compose build --no-cache'

# Shell access to container
alias ai_docker_shell='docker run -it --rm -v "$SCRIPT_DIR:/app" -w /app cli_tools-ai-tools-api /bin/bash'

# Clean up Docker resources
alias ai_docker_clean='docker-compose down -v && docker system prune -f'

# =============================================================================
# Help
# =============================================================================

ai_docker_help() {
    echo ""
    echo "AI Tools Docker Commands:"
    echo ""
    echo "API Service Management:"
    echo "  ai_api_start        - Start API service"
    echo "  ai_api_stop         - Stop API service"
    echo "  ai_api_logs         - View API logs"
    echo "  ai_api_restart      - Restart API service"
    echo "  ai_api_build        - Build and start API"
    echo "  ai_api_health       - Check API health"
    echo ""
    echo "CLI Commands (run in Docker):"
    echo "  ai_tools_docker     - Main CLI tool (add subcommand: convert/github/youtube)"
    echo "  ai_convert_docker   - Convert PDF to markdown"
    echo "  ai_github_docker    - Analyze GitHub PRs"
    echo "  ai_youtube_docker   - Analyze YouTube videos"
    echo "  ngit_docker         - Structured git workflow"
    echo "  pr_review_docker    - PR reviewer tool"
    echo ""
    echo "Utilities:"
    echo "  ai_docker_rebuild   - Rebuild Docker images from scratch"
    echo "  ai_docker_shell     - Get shell access to container"
    echo "  ai_docker_clean     - Clean up Docker resources"
    echo "  ai_docker_help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ai_convert_docker input.pdf --format enhanced --clipboard"
    echo "  ai_github_docker https://github.com/owner/repo/pull/123 --target slack"
    echo "  ai_youtube_docker 'https://youtu.be/VIDEO_ID' --save-file --dynamic-tags"
    echo ""
}

# Show help on load
ai_docker_help