# Guides

[Home](../README.md) > Guides

In-depth guides for common workflows and advanced usage.

## Available Guides

| Guide | Description |
|-------|-------------|
| [YouTube Analysis](youtube-analysis.md) | Deep dive into video analysis features |
| [PR Review](pr-review.md) | GitHub pull request review workflows |
| [Batch Processing](batch-processing.md) | Working with multiple files and playlists |

## Guide Overview

### [YouTube Analysis](youtube-analysis.md)

Learn how to:
- Extract and analyze video content
- Generate meaningful summaries
- Work with different languages
- Handle videos without transcripts

**Related commands:** [youtube](../commands/youtube.md), [process-playlist](../commands/process-playlist.md)

### [PR Review](pr-review.md)

Learn how to:
- Analyze pull requests effectively
- Interpret review results
- Integrate with your workflow
- Use different output formats

**Related command:** [github](../commands/github.md)

### [Batch Processing](batch-processing.md)

Learn how to:
- Process multiple videos efficiently
- Handle playlists
- Deal with errors and rate limits
- Organize output files

**Related commands:** [youtube](../commands/youtube.md), [process-playlist](../commands/process-playlist.md)

## Quick Tips

### Choosing an LLM Provider

| Provider | Best For |
|----------|----------|
| DeepSeek | Cost-effective batch processing |
| Anthropic | Highest quality analysis |

```bash
# Use DeepSeek for batch jobs
ai process-playlist "URL" --llm-provider deepseek

# Use Anthropic for important reviews
ai github "PR_URL" --llm-provider anthropic
```

### Saving Time

- Use `--dry-run` to preview before processing
- Process playlists during off-peak hours
- Use DeepSeek for large batches to save money

## Related

- [Commands Reference](../commands/README.md) - All commands
- [Configuration](../getting-started/configuration.md) - API keys setup
- [API Reference](../api/README.md) - Programmatic access
