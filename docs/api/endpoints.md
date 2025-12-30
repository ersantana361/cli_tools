# API Endpoints

[Home](../README.md) > [API Reference](README.md) > Endpoints

Complete reference for all REST API endpoints.

## Health Check

### GET /health

Check if the API server is running.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

## YouTube Analysis

### POST /api/v1/youtube/analyze

Analyze a YouTube video.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/youtube/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "video": "https://youtu.be/VIDEO_ID",
    "language": "en",
    "target": "markdown",
    "dynamic_tags": true,
    "llm_provider": "deepseek"
  }'
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `video` | string | Yes | - | YouTube video URL |
| `language` | string | No | `"en"` | Transcript language |
| `target` | string | No | `"markdown"` | Output format (`markdown`/`slack`) |
| `dynamic_tags` | boolean | No | `false` | Generate content tags |
| `llm_provider` | string | No | `"anthropic"` | LLM provider |
| `prompt_only` | boolean | No | `false` | Return prompt without analysis |

**Response:**
```json
{
  "success": true,
  "analysis": "# Video Title\n\n## Introduction\n...",
  "error": null
}
```

**Errors:**

| Code | Description |
|------|-------------|
| 400 | Invalid request (missing video URL) |
| 404 | Video not found |
| 500 | Analysis failed |

---

## PDF Conversion

### POST /api/v1/convert/pdf

Convert a PDF to Markdown.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/convert/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "input_source": "https://example.com/document.pdf",
    "format": "enhanced"
  }'
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `input_source` | string | Yes | - | PDF URL or path |
| `format` | string | No | `"basic"` | Format mode (`basic`/`enhanced`) |

**Response:**
```json
{
  "success": true,
  "content": "# Document Title\n\n...",
  "error": null
}
```

---

## GitHub PR Analysis

### POST /api/v1/github/analyze-pr

Analyze a GitHub pull request.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/github/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{
    "pr_url": "https://github.com/owner/repo/pull/123",
    "target": "github",
    "llm_provider": "anthropic"
  }'
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `pr_url` | string | Yes | - | GitHub PR URL |
| `target` | string | No | `"github"` | Output format (`github`/`slack`) |
| `llm_provider` | string | No | `"anthropic"` | LLM provider |

**Response:**
```json
{
  "success": true,
  "analysis": "## PR Analysis\n\n### Summary\n...",
  "error": null
}
```

**Errors:**

| Code | Description |
|------|-------------|
| 400 | Invalid PR URL |
| 401 | GitHub authentication failed |
| 404 | PR not found |
| 500 | Analysis failed |

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "success": false,
  "analysis": null,
  "error": "Error description here"
}
```

### Common Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Authentication failed |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## Rate Limits

The API inherits rate limits from external services:

| Service | Limit |
|---------|-------|
| YouTube API | ~10,000 units/day |
| GitHub API | 5,000 requests/hour |
| Anthropic | Varies by plan |
| DeepSeek | Varies by plan |

---

## Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/youtube/analyze",
    json={
        "video": "https://youtu.be/VIDEO_ID",
        "llm_provider": "deepseek"
    }
)

data = response.json()
if data["success"]:
    print(data["analysis"])
else:
    print(f"Error: {data['error']}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/youtube/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    video: 'https://youtu.be/VIDEO_ID',
    llm_provider: 'deepseek'
  })
});

const data = await response.json();
if (data.success) {
  console.log(data.analysis);
} else {
  console.error(data.error);
}
```

---

## Related

- [API Overview](README.md) - Server setup
- [Configuration](../getting-started/configuration.md) - Environment variables
- [Commands Reference](../commands/README.md) - CLI alternative
