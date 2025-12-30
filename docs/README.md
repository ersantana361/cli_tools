# CLI Tools Documentation

AI-powered command-line tools for YouTube analysis, PDF conversion, GitHub PR review, and more.

## Quick Links

| I want to... | Go to |
|--------------|-------|
| Get started quickly | [Quick Start](getting-started/quick-start.md) |
| Set up Docker | [Installation](getting-started/installation.md) |
| Configure API keys | [Configuration](getting-started/configuration.md) |
| Analyze a YouTube video | [youtube command](commands/youtube.md) |
| Process a playlist | [process-playlist command](commands/process-playlist.md) |
| Convert a PDF | [convert command](commands/convert.md) |
| Review a GitHub PR | [github command](commands/github.md) |
| Use the REST API | [API Reference](api/README.md) |

## Documentation Sections

### [Getting Started](getting-started/README.md)

Everything you need to start using the CLI tools.

- [Installation](getting-started/installation.md) - Docker setup and dependencies
- [Quick Start](getting-started/quick-start.md) - Your first commands
- [Configuration](getting-started/configuration.md) - Environment variables and LLM providers

### [Commands](commands/README.md)

Reference documentation for all CLI commands.

- [youtube](commands/youtube.md) - Analyze YouTube videos
- [process-playlist](commands/process-playlist.md) - Batch process YouTube playlists
- [convert](commands/convert.md) - Convert PDFs to Markdown
- [github](commands/github.md) - Analyze GitHub pull requests

### [Guides](guides/README.md)

In-depth guides for common workflows.

- [YouTube Analysis](guides/youtube-analysis.md) - Deep dive into video analysis features
- [PR Review](guides/pr-review.md) - GitHub pull request review workflows
- [Batch Processing](guides/batch-processing.md) - Working with multiple files

### [API Reference](api/README.md)

REST API documentation for programmatic access.

- [Endpoints](api/endpoints.md) - All available API endpoints

## Command Overview

```bash
# Set up the alias (add to ~/.bashrc)
alias ai='/path/to/cli_tools/docker-run.sh'

# Available commands
ai youtube "VIDEO_URL"              # Analyze a video
ai process-playlist "PLAYLIST_URL"  # Process entire playlist
ai convert file.pdf                 # Convert PDF to Markdown
ai github "PR_URL"                  # Analyze a pull request
```

## Requirements

- Docker and Docker Compose
- API keys for LLM providers (Anthropic or DeepSeek)
- YouTube API key (for playlist features)
- GitHub token (for PR analysis)

See [Configuration](getting-started/configuration.md) for details.
