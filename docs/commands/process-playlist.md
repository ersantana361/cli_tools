# process-playlist Command

[Home](../README.md) > [Commands](README.md) > process-playlist

Batch process all videos in a YouTube playlist, generating summary files for each.

## Usage

```bash
ai process-playlist "PLAYLIST_URL" [options]
```

## Examples

### Basic Usage

```bash
ai process-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

Processes all videos and saves markdown files to `./summaries/`.

### Preview Videos (Dry Run)

```bash
ai process-playlist "PLAYLIST_URL" --dry-run
```

Lists all videos in the playlist without processing them.

### Custom Output Directory

```bash
ai process-playlist "PLAYLIST_URL" --output-dir ./my-summaries
```

### Using DeepSeek

```bash
ai process-playlist "PLAYLIST_URL" --llm-provider deepseek
```

### Spanish Transcripts

```bash
ai process-playlist "PLAYLIST_URL" --language es
```

### Without Dynamic Tags

```bash
ai process-playlist "PLAYLIST_URL" --no-tags
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir, -o` | Output directory for files | `./summaries` |
| `--dry-run` | List videos without processing | disabled |
| `--language, -l` | Transcript language code | `en` |
| `--no-tags` | Disable dynamic tag generation | tags enabled |
| `--llm-provider` | LLM provider (`anthropic`/`deepseek`) | `anthropic` |

## Behavior

### Fail-Fast Processing

The command stops on the first failure. This prevents wasting API calls when there's an issue.

```
Processing 10 video(s)...
Video 1/10 ━━━━━━━━━━━━━━━━━━━━ 100%

============================================================
╭─────────── Summary ───────────╮
│ Stopped on failure            │
│                               │
│ ✅ Successful: 3              │
│ ❌ Failed: 1                  │
│ 📊 Processed: 4/10            │
╰───────────────────────────────╯
```

### Output Files

Files are named after video titles with sanitized characters:

```
summaries/
├── Introduction-to-Machine-Learning.md
├── Deep-Learning-Fundamentals.md
└── Neural-Networks-Explained.md
```

### Progress Display

```
Extracting videos from playlist...
Found 10 videos

Output directory: /path/to/summaries

Processing 10 video(s)...
Video 3/10 ━━━━━━━━━━━━━━━━━━━━ 30% • 3/10 0:02:15
```

## Requirements

- `YOUTUBE_API_KEY` environment variable (for playlist extraction)
- `DEEPSEEK_API_KEY` or `ANTHROPIC_API_KEY` (for LLM analysis)

See [Configuration](../getting-started/configuration.md) for setup.

## Comparison with youtube Command

| Feature | youtube | process-playlist |
|---------|---------|------------------|
| Single video | ✅ | ❌ |
| Multiple videos | ✅ (with URLs) | ✅ (from playlist) |
| Playlist support | ✅ (inline) | ✅ (dedicated) |
| Dry run | ❌ | ✅ |
| Custom output dir | ❌ | ✅ |
| Fail-fast | ✅ | ✅ |

Use `process-playlist` when you have a playlist URL and want a simpler interface.

## Troubleshooting

### "YOUTUBE_API_KEY not set"

Set up your YouTube API key. See [Configuration](../getting-started/configuration.md#youtube-api-key).

### "Invalid playlist URL"

Make sure the URL contains `list=` parameter:
- ✅ `https://www.youtube.com/playlist?list=PLxxxxxxx`
- ✅ `https://www.youtube.com/watch?v=xxx&list=PLxxxxxxx`
- ❌ `https://www.youtube.com/watch?v=xxx`

### Rate limiting

YouTube may block requests if you process too many videos quickly. The command includes a 0.5s delay between videos, but you may need to wait if blocked.

## Related

- [youtube](youtube.md) - Single video analysis
- [Batch Processing Guide](../guides/batch-processing.md) - In-depth batch workflows
- [YouTube Analysis Guide](../guides/youtube-analysis.md) - Analysis features
- [Configuration](../getting-started/configuration.md) - API keys setup
