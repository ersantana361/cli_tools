# AI Tools API

This API provides REST endpoints for PDF conversion, GitHub PR analysis, and YouTube content analysis.

## Quick Start

### Docker Setup (Recommended)

1. **Build and start the API:**
```bash
docker-compose up -d
```

2. **Check API health:**
```bash
curl http://localhost:8000/health
```

3. **Use the API:**
```bash
# PDF conversion
curl -X POST "http://localhost:8000/api/v1/convert/pdf" \
  -H "Content-Type: application/json" \
  -d '{"input_source": "path/to/file.pdf", "format": "enhanced"}'

# GitHub PR analysis
curl -X POST "http://localhost:8000/api/v1/github/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{"pr_link": "https://github.com/owner/repo/pull/123", "llm_provider": "anthropic"}'

# YouTube analysis
curl -X POST "http://localhost:8000/api/v1/youtube/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video": "https://youtu.be/VIDEO_ID", "target": "markdown"}'
```

### Environment Variables

Required environment variables in `.env` file:
```
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
GITHUB_TOKEN_WORK=your_github_token
YOUTUBE_API_KEY=your_youtube_key
SLACK_TOKEN=your_slack_token
```

### Docker Aliases

Source the provided aliases for easier management:
```bash
source scripts/docker-aliases.sh
```

Available aliases:
- `ai_api_start` - Start API service
- `ai_api_stop` - Stop API service
- `ai_api_logs` - View API logs
- `ai_api_restart` - Restart API service
- `ai_api_build` - Build and start API
- `ai_api_health` - Check API health

### CLI Client

Use the provided CLI client that talks to the API:
```bash
# Convert PDF
python scripts/api_client.py convert input.pdf -o output.md --format enhanced

# Analyze GitHub PR
python scripts/api_client.py github https://github.com/owner/repo/pull/123 --llm-provider anthropic

# Analyze YouTube video
python scripts/api_client.py youtube "https://youtu.be/VIDEO_ID" --dynamic-tags
```

## API Endpoints

### Health Check
- **GET** `/health`
- Returns API status and version

### PDF Conversion
- **POST** `/api/v1/convert/pdf`
- Convert PDF to Markdown format

### GitHub PR Analysis
- **POST** `/api/v1/github/analyze-pr`
- Analyze GitHub pull requests with AI

### YouTube Analysis
- **POST** `/api/v1/youtube/analyze`
- Analyze YouTube video content

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python api/server.py
```

### API Documentation
Once running, visit:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Migration from CLI

Your existing CLI aliases will continue to work. The API provides an additional interface while maintaining full backward compatibility with the original CLI tools.