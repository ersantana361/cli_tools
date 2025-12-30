# API Reference

[Home](../README.md) > API Reference

REST API documentation for programmatic access to CLI tools.

## Overview

The CLI tools include a FastAPI-based REST service for integration with other applications.

## Quick Start

### Start the API Server

```bash
# Using Docker Compose
docker-compose up -d ai-tools-api

# Check health
curl http://localhost:8000/health
```

### Make a Request

```bash
curl -X POST http://localhost:8000/api/v1/youtube/analyze \
  -H "Content-Type: application/json" \
  -d '{"video": "https://youtu.be/VIDEO_ID"}'
```

## Endpoints

See [Endpoints Reference](endpoints.md) for complete documentation.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/youtube/analyze` | POST | Analyze YouTube video |
| `/api/v1/convert/pdf` | POST | Convert PDF to Markdown |
| `/api/v1/github/analyze-pr` | POST | Analyze GitHub PR |

## Authentication

The API uses environment variables for authentication with external services (YouTube, GitHub, LLM providers). No API key is required to call the local endpoints.

## Response Format

All endpoints return JSON:

```json
{
  "success": true,
  "analysis": "...",
  "error": null
}
```

### Success Response

```json
{
  "success": true,
  "analysis": "# Video Analysis\n\n...",
  "error": null
}
```

### Error Response

```json
{
  "success": false,
  "analysis": null,
  "error": "Video not found"
}
```

## Server Management

### Start Server

```bash
docker-compose up -d ai-tools-api
```

### Stop Server

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f ai-tools-api
```

### Using Aliases

```bash
source scripts/docker-aliases.sh

ai_api_start    # Start
ai_api_stop     # Stop
ai_api_logs     # View logs
ai_api_health   # Check health
```

## Configuration

The API server uses the same environment variables as the CLI:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API |
| `DEEPSEEK_API_KEY` | DeepSeek API |
| `YOUTUBE_API_KEY` | YouTube Data API |
| `GITHUB_TOKEN_WORK` | GitHub API |

See [Configuration](../getting-started/configuration.md) for details.

## Related

- [Endpoints Reference](endpoints.md) - Detailed endpoint documentation
- [Configuration](../getting-started/configuration.md) - Environment variables
- [Commands Reference](../commands/README.md) - CLI alternative
