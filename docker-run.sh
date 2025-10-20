#!/bin/bash
# docker-run.sh - Wrapper script to run CLI tools in Docker containers
# Usage: ./docker-run.sh <command> [args...]
# Example: ./docker-run.sh ai_tools convert input.pdf --format enhanced

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Docker image name
IMAGE_NAME="cli_tools-ai-tools-api"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if image exists, if not build it
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    print_warning "Docker image not found. Building it now..."
    docker-compose build
    print_success "Image built successfully"
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Prepare environment variables
ENV_VARS=""
if [ -n "$ANTHROPIC_API_KEY" ]; then
    ENV_VARS="$ENV_VARS -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
fi
if [ -n "$DEEPSEEK_API_KEY" ]; then
    ENV_VARS="$ENV_VARS -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY"
fi
if [ -n "$GITHUB_TOKEN_WORK" ]; then
    ENV_VARS="$ENV_VARS -e GITHUB_TOKEN_WORK=$GITHUB_TOKEN_WORK"
fi
if [ -n "$YOUTUBE_API_KEY" ]; then
    ENV_VARS="$ENV_VARS -e YOUTUBE_API_KEY=$YOUTUBE_API_KEY"
fi
if [ -n "$SLACK_TOKEN" ]; then
    ENV_VARS="$ENV_VARS -e SLACK_TOKEN=$SLACK_TOKEN"
fi
if [ -n "$DISPLAY" ]; then
    ENV_VARS="$ENV_VARS -e DISPLAY=$DISPLAY"
fi

# Prepare volume mounts
VOLUME_MOUNTS="-v $SCRIPT_DIR:/app -v $SCRIPT_DIR/workspace:/workspace"

# Mount .claude directory if it exists
if [ -d "$HOME/.claude" ]; then
    VOLUME_MOUNTS="$VOLUME_MOUNTS -v $HOME/.claude:/home/appuser/.claude:ro"
fi

# Mount X11 socket for clipboard support if available
if [ -d "/tmp/.X11-unix" ]; then
    VOLUME_MOUNTS="$VOLUME_MOUNTS -v /tmp/.X11-unix:/tmp/.X11-unix:ro"
fi

# Check if no arguments provided
if [ $# -eq 0 ]; then
    print_error "No command provided"
    echo ""
    echo "Usage: ./docker-run.sh <command> [args...]"
    echo ""
    echo "Examples:"
    echo "  ./docker-run.sh python ai_tools/main.py convert input.pdf --format enhanced"
    echo "  ./docker-run.sh python ai_tools/main.py github https://github.com/owner/repo/pull/123"
    echo "  ./docker-run.sh python ai_tools/main.py youtube 'https://youtu.be/VIDEO_ID' --save-file"
    echo "  ./docker-run.sh python ngit/main.py"
    echo ""
    exit 1
fi

# Run the command in Docker
print_info "Running command in Docker container..."
docker run --rm -it \
    $ENV_VARS \
    $VOLUME_MOUNTS \
    -w /app \
    "$IMAGE_NAME" \
    "$@"
