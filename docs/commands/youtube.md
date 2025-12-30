# youtube Command

[Home](../README.md) > [Commands](README.md) > youtube

Analyze YouTube videos using AI to generate summaries, breakdowns, and insights.

## Usage

```bash
ai youtube "VIDEO_URL" [options]
```

## Examples

### Basic Analysis

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID"
```

Analyzes the video and copies the result to clipboard.

### Save to File

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file
```

Saves analysis to a markdown file named after the video title.

### With Dynamic Tags

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --dynamic-tags
```

Generates YAML front matter with content-based tags.

### Using DeepSeek

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --llm-provider deepseek
```

### Custom Output File

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file -o my-analysis.md
```

### Different Language

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --language es
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--save-file` | Save output to markdown file | clipboard only |
| `-o, --output` | Custom output filename | auto from title |
| `--language, -l` | Transcript language code | `en` |
| `--dynamic-tags` | Generate content-based tags | disabled |
| `--llm-provider` | LLM provider (`anthropic`/`deepseek`) | `anthropic` |
| `--prompt-only` | Generate prompt without analysis | disabled |
| `--target` | Output format (`markdown`/`slack`) | `markdown` |

## Output Format

The generated markdown includes:

```markdown
---
tags:
  - ai
  - machine-learning
  - tutorial
---

# Video Title

## Introduction
Overview of the video content...

## Detailed Analysis
Time-stamped breakdown of key sections...

## Key Takeaways
Main points and conclusions...
```

## How It Works

1. **Transcript Extraction** - Fetches video captions via YouTube API
2. **Language Fallback** - Tries requested language, then English, then any available
3. **AI Analysis** - Sends transcript to LLM for structured analysis
4. **Tag Generation** - (Optional) Generates relevant tags from content
5. **Output** - Saves to file or copies to clipboard

## Batch Processing

For multiple videos, use [process-playlist](process-playlist.md) or provide multiple URLs:

```bash
ai youtube "URL1" "URL2" "URL3" --save-file
```

Note: Multiple URLs require `--save-file` flag.

## Troubleshooting

### No transcript available

Some videos don't have captions. You'll be prompted to:
- Continue with title-only analysis
- Provide a manual transcript

### Rate limiting

If YouTube blocks requests, wait a few minutes and try again. See [Batch Processing Guide](../guides/batch-processing.md) for rate limiting tips.

### LLM errors

Check your API keys in [Configuration](../getting-started/configuration.md).

## Related

- [process-playlist](process-playlist.md) - Batch process playlists
- [YouTube Analysis Guide](../guides/youtube-analysis.md) - In-depth workflows
- [Batch Processing Guide](../guides/batch-processing.md) - Working with multiple videos
- [Configuration](../getting-started/configuration.md) - API keys setup
