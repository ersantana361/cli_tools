#!/bin/bash
# Docker aliases for AI Tools API

# Start the API service
alias ai_api_start='docker-compose up -d'

# Stop the API service
alias ai_api_stop='docker-compose down'

# View API logs
alias ai_api_logs='docker-compose logs -f ai-tools-api'

# Restart API service
alias ai_api_restart='docker-compose restart ai-tools-api'

# CLI commands that call the API (requires running API service)
alias ai_tools_api="python /home/ersantana/dev/projects/personal/cli_tools/scripts/api_client.py"

# Build and start API
alias ai_api_build='docker-compose build && docker-compose up -d'

# Check API health
alias ai_api_health='curl -s http://localhost:8000/health | jq'

echo "AI Tools Docker aliases loaded:"
echo "  ai_api_start    - Start API service"
echo "  ai_api_stop     - Stop API service"
echo "  ai_api_logs     - View API logs"
echo "  ai_api_restart  - Restart API service"
echo "  ai_api_build    - Build and start API"
echo "  ai_api_health   - Check API health"