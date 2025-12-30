# Quick Start

[Home](../README.md) > [Getting Started](README.md) > Quick Start

Get up and running in 5 minutes.

## 1. Set Up the Alias

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
# Using relative path (run from cli_tools directory)
alias ai='./docker-run.sh'

# Or using absolute path (run from anywhere)
alias ai='/path/to/cli_tools/docker-run.sh'
```

Reload your shell:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

## 2. Set Environment Variables

Add your API keys (see [Configuration](configuration.md) for details):

```bash
export DEEPSEEK_API_KEY="your_key"      # Required for LLM
export YOUTUBE_API_KEY="your_key"       # Required for playlists
export ANTHROPIC_API_KEY="your_key"     # Alternative LLM
export GITHUB_TOKEN_WORK="your_token"   # For PR analysis
```

## 3. Try Your First Command

### Analyze a YouTube Video

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --llm-provider deepseek
```

This will:
1. Fetch the video transcript
2. Generate an AI analysis
3. Save it to a markdown file

### Preview a Playlist

```bash
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --dry-run
```

### Convert a PDF

```bash
ai convert document.pdf --format enhanced --clipboard
```

### Analyze a GitHub PR

```bash
ai github "https://github.com/owner/repo/pull/123"
```

## 4. View Help

```bash
# General help
ai --help

# Command-specific help
ai youtube --help
ai process-playlist --help
ai convert --help
ai github --help
```

## Common Options

| Option | Description |
|--------|-------------|
| `--llm-provider` | Choose `anthropic` or `deepseek` |
| `--save-file` | Save output to file |
| `--dry-run` | Preview without processing |
| `--help` | Show command help |

## Next Steps

- [Configuration](configuration.md) - Full configuration options
- [youtube command](../commands/youtube.md) - YouTube analysis details
- [process-playlist command](../commands/process-playlist.md) - Batch playlist processing
- [Guides](../guides/README.md) - In-depth workflows

## Troubleshooting

### "command not found: ai"

Make sure you've:
1. Added the alias to your shell config
2. Reloaded the shell (`source ~/.bashrc`)

### API errors

Check that your environment variables are set:

```bash
echo $DEEPSEEK_API_KEY
echo $YOUTUBE_API_KEY
```

See [Configuration](configuration.md) for more details.
