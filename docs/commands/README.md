# Commands Reference

[Home](../README.md) > Commands

Complete reference for all CLI commands.

## Available Commands

| Command | Description | Guide |
|---------|-------------|-------|
| [youtube](youtube.md) | Analyze YouTube videos | [YouTube Analysis](../guides/youtube-analysis.md) |
| [process-playlist](process-playlist.md) | Batch process YouTube playlists | [Batch Processing](../guides/batch-processing.md) |
| [convert](convert.md) | Convert PDFs to Markdown | - |
| [github](github.md) | Analyze GitHub pull requests | [PR Review](../guides/pr-review.md) |

## Quick Reference

```bash
# YouTube - single video
ai youtube "VIDEO_URL" --save-file --dynamic-tags

# YouTube - playlist
ai process-playlist "PLAYLIST_URL" --output-dir ./summaries

# PDF conversion
ai convert file.pdf --format enhanced --clipboard

# GitHub PR
ai github "PR_URL" --target github
```

## Common Options

These options work across multiple commands:

| Option | Description | Commands |
|--------|-------------|----------|
| `--llm-provider` | LLM to use (`anthropic` or `deepseek`) | all |
| `--save-file` | Save output to file | youtube |
| `--dry-run` | Preview without processing | process-playlist |
| `--help` | Show command help | all |

## Getting Help

```bash
# List all commands
ai --help

# Command-specific help
ai youtube --help
ai process-playlist --help
ai convert --help
ai github --help
```

## Related

- [Quick Start](../getting-started/quick-start.md) - First commands
- [Configuration](../getting-started/configuration.md) - API keys setup
- [Guides](../guides/README.md) - In-depth workflows
