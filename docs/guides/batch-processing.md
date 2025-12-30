# Batch Processing Guide

[Home](../README.md) > [Guides](README.md) > Batch Processing

Guide to processing multiple files and handling batch operations efficiently.

## Overview

Batch processing allows you to analyze multiple YouTube videos in a single command, with automatic progress tracking and error handling.

## Methods

### 1. Process a Playlist

```bash
ai process-playlist "PLAYLIST_URL" --output-dir ./summaries
```

Best for: YouTube playlists with known structure.

### 2. Multiple URLs

```bash
ai youtube "URL1" "URL2" "URL3" --save-file
```

Best for: Specific videos from different sources.

## Fail-Fast Behavior

Batch processing **stops on the first failure**. This design:
- Saves API credits when there's an issue
- Prevents processing invalid data
- Allows you to fix problems before continuing

### Example Output

```
Processing 10 video(s)...
Video 4/10 ━━━━━━━━━━━━━━━━━━━━ 40%

============================================================
╭─────────── Summary ───────────╮
│ Stopped on failure            │
│                               │
│ ✅ Successful: 3              │
│ ❌ Failed: 1                  │
│ 📊 Processed: 4/10            │
╰───────────────────────────────╯

Failed Videos:
  • Video Title Here
    Error: No transcript available
```

### Handling Failures

After a failure:

1. **Check the error message** - Common issues:
   - No transcript available
   - Rate limiting
   - API key issues

2. **Fix the issue** - See troubleshooting below

3. **Resume processing** - Re-run with remaining URLs

## Planning Large Batches

### Preview First

Always preview before processing:

```bash
ai process-playlist "URL" --dry-run
```

This shows:
- Number of videos
- Video URLs
- No API calls made

### Estimate Costs

| Videos | DeepSeek Cost | Anthropic Cost |
|--------|---------------|----------------|
| 10 | ~$0.10 | ~$1.00 |
| 50 | ~$0.50 | ~$5.00 |
| 100 | ~$1.00 | ~$10.00 |

*Estimates vary based on video length and transcript size.*

### Choose the Right Provider

```bash
# Use DeepSeek for large batches (cost-effective)
ai process-playlist "URL" --llm-provider deepseek

# Use Anthropic for important content (higher quality)
ai youtube "IMPORTANT_VIDEO" --llm-provider anthropic
```

## Handling Rate Limits

### YouTube Rate Limits

YouTube may block requests if you:
- Process too many videos quickly
- Make requests from cloud IPs

**Symptoms:**
```
Could not retrieve a transcript for the video...
YouTube is blocking requests from your IP
```

**Solutions:**

1. **Wait** - Rate limits reset after 15-30 minutes

2. **Use smaller batches** - Process 10-20 videos at a time

3. **Add delays** - The tool adds 0.5s between videos automatically

### LLM Rate Limits

Both Anthropic and DeepSeek have rate limits.

**Solutions:**
- Use DeepSeek (higher limits)
- Wait between large batches
- Check your API tier

## File Organization

### Default Structure

```bash
ai process-playlist "URL" --output-dir ./course-videos
```

Creates:
```
course-videos/
├── Lecture-1-Introduction.md
├── Lecture-2-Fundamentals.md
├── Lecture-3-Advanced-Topics.md
└── ...
```

### Naming Convention

Files are named from video titles:
- Special characters removed
- Spaces become dashes
- Maximum 100 characters

```
Original: "Python Tutorial #1: Getting Started! (2024)"
Filename: Python-Tutorial-1-Getting-Started-2024.md
```

## Best Practices

### Before Processing

- [ ] Preview with `--dry-run`
- [ ] Check video count
- [ ] Verify API keys are set
- [ ] Choose appropriate LLM provider
- [ ] Create output directory

### During Processing

- Monitor progress
- Note any failures
- Don't interrupt unless necessary

### After Processing

- [ ] Check success/failure count
- [ ] Review failed videos
- [ ] Spot-check generated files
- [ ] Re-process failed videos if needed

## Troubleshooting

### "IP blocked by YouTube"

**Cause:** Too many transcript requests.

**Fix:**
1. Wait 15-30 minutes
2. Process smaller batches
3. Use a VPN if persistent

### "No transcript available"

**Cause:** Video has no captions.

**Fix:**
- Skip the video
- Provide manual transcript
- Check if captions exist on YouTube

### "LLM credit balance too low"

**Cause:** API account needs credits.

**Fix:**
1. Add credits to your account
2. Switch to another provider:
   ```bash
   ai process-playlist "URL" --llm-provider deepseek
   ```

### "Processing stopped unexpectedly"

**Cause:** Network issue or API error.

**Fix:**
1. Check internet connection
2. Verify API keys
3. Check API service status
4. Re-run the command

## Related

- [youtube command](../commands/youtube.md) - Single video analysis
- [process-playlist command](../commands/process-playlist.md) - Playlist processing
- [YouTube Analysis Guide](youtube-analysis.md) - Analysis features
- [Configuration](../getting-started/configuration.md) - API keys setup
