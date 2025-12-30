# YouTube Analysis Guide

[Home](../README.md) > [Guides](README.md) > YouTube Analysis

Deep dive into analyzing YouTube videos with AI.

## Overview

The YouTube analysis tools extract video transcripts and use AI to generate structured summaries, key takeaways, and insights.

## Basic Workflow

### 1. Single Video Analysis

```bash
ai youtube "https://www.youtube.com/watch?v=VIDEO_ID" --save-file --dynamic-tags
```

This generates a markdown file with:
- YAML front matter with tags
- Introduction and overview
- Time-stamped content breakdown
- Key takeaways

### 2. Playlist Analysis

```bash
# Preview first
ai process-playlist "PLAYLIST_URL" --dry-run

# Then process
ai process-playlist "PLAYLIST_URL" --output-dir ./video-summaries
```

## Understanding the Output

### YAML Front Matter

When using `--dynamic-tags`:

```yaml
---
tags:
  - machine-learning
  - python
  - tutorial
  - beginner
---
```

Tags are generated based on content analysis.

### Analysis Sections

**Introduction**
- Video objectives
- Target audience
- Main themes

**Detailed Analysis**
- Chronological breakdown
- Key timestamps
- Important quotes or examples

**Conclusion**
- Main takeaways
- Practical applications
- Recommendations

## Working with Languages

### Specifying Language

```bash
ai youtube "VIDEO_URL" --language es  # Spanish
ai youtube "VIDEO_URL" --language fr  # French
ai youtube "VIDEO_URL" --language de  # German
```

### Language Fallback

If the requested language isn't available:
1. Tries manual transcripts in requested language
2. Falls back to auto-generated transcripts
3. Falls back to English
4. Falls back to any available language

## Handling Missing Transcripts

Some videos don't have captions. When this happens:

```
╭────────────────── Transcript Issue ──────────────────╮
│ ⚠️ No Transcript Available                            │
│                                                      │
│ This video doesn't have usable captions/transcripts. │
│ You can either:                                      │
│ • Continue with video title and URL only             │
│ • Provide a manual transcript/summary                │
╰──────────────────────────────────────────────────────╯
```

**Options:**
- Continue with title-only analysis (limited)
- Provide your own transcript or notes
- Skip the video

## Optimizing for Cost

### Use DeepSeek for Batches

```bash
ai process-playlist "URL" --llm-provider deepseek
```

DeepSeek is significantly cheaper for large batches.

### Skip Tags for Speed

```bash
ai process-playlist "URL" --no-tags
```

Tag generation requires an additional LLM call per video.

## File Organization

### Default Naming

Files are named from video titles:

```
Original: "Introduction to Machine Learning | Part 1"
Filename: Introduction-to-Machine-Learning-Part-1.md
```

Special characters are removed, spaces become dashes.

### Custom Output Directory

```bash
ai process-playlist "URL" --output-dir ./courses/ml-basics/
```

Creates the directory if it doesn't exist.

## Best Practices

### Before Processing

1. **Preview the playlist**
   ```bash
   ai process-playlist "URL" --dry-run
   ```

2. **Check video count** - Large playlists take time and API credits

3. **Verify API keys** - Ensure YouTube and LLM keys are set

### During Processing

- Processing is **fail-fast** - stops on first error
- Videos are processed sequentially with 0.5s delay
- Progress is shown in real-time

### After Processing

- Review generated files for quality
- Check failed videos in the summary
- Re-run with specific URLs if needed

## Troubleshooting

### "IP blocked by YouTube"

YouTube may block transcript requests from cloud IPs or after too many requests.

**Solutions:**
- Wait 15-30 minutes
- Use a VPN
- Process fewer videos at once

### "No transcript available"

The video doesn't have captions.

**Solutions:**
- Check if captions exist on YouTube
- Try a different language
- Provide manual transcript

### "LLM API error"

Check your API key balance and validity.

```bash
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
```

## Related

- [youtube command](../commands/youtube.md) - Command reference
- [process-playlist command](../commands/process-playlist.md) - Playlist processing
- [Batch Processing Guide](batch-processing.md) - Handling multiple files
- [Configuration](../getting-started/configuration.md) - API keys setup
