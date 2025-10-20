# YouTube Batch Processing & File Saving Features

## Overview
Added support for batch processing multiple YouTube videos and automatic markdown file generation.

## New Features

### 1. File Saving
- Save YouTube video analyses to individual `.md` files
- Automatic filename generation from video title
- Custom filename support for single videos
- Safe filename sanitization (removes special characters, truncates long names)

### 2. Playlist Support
- Extract all videos from YouTube playlist URLs
- Automatic pagination for large playlists
- Process entire playlists with one command

### 3. Batch Processing
- Process multiple videos in a single command
- Real-time progress tracking with Rich progress bar
- Automatic rate limiting between videos
- Comprehensive error handling (continues on failure)
- Summary report at completion

## Usage Examples

### Single Video (Clipboard Only - Default)
```bash
python ai_tools/main.py youtube "https://youtu.be/VIDEO_ID"
```

Output: Analysis copied to clipboard, displayed in console

### Single Video with File Save
```bash
python ai_tools/main.py youtube "https://youtu.be/VIDEO_ID" --save-file
```

Output: Creates `Video-Title-Here.md` in current directory + clipboard

💡 **Note**: `--save-file` automatically uses markdown format. You'll see: `📄 Saving to markdown file(s)`

### Multiple Videos (Requires --save-file)
```bash
python ai_tools/main.py youtube \
  "https://youtu.be/VIDEO_ID_1" \
  "https://youtu.be/VIDEO_ID_2" \
  "https://youtu.be/VIDEO_ID_3" \
  --save-file
```

Output: Creates separate `.md` files for each video

⚠️ **Note**: The `--save-file` flag is **required** for batch processing. Multiple analyses cannot be output to clipboard only.

### Playlist Processing (Requires --save-file)
```bash
python ai_tools/main.py youtube \
  "https://www.youtube.com/playlist?list=PLAYLIST_ID" \
  --save-file
```

Output: Creates `.md` files for all videos in the playlist

⚠️ **Note**: The `--save-file` flag is **required** for playlists. Multiple analyses cannot be output to clipboard only.

### Single Video with Custom Filename
```bash
python ai_tools/main.py youtube "https://youtu.be/VIDEO_ID" \
  --save-file \
  -o my-custom-name.md
```

### Advanced Options
```bash
python ai_tools/main.py youtube "URL1" "URL2" \
  --save-file \
  --dynamic-tags \
  --llm-provider anthropic \
  --language en
```

💡 **Note**: `--target markdown` is now automatic when using `--save-file`, so you don't need to specify it!

## Implementation Details

### Modified Files

1. **`ai_tools/tools/youtube_utils.py`**
   - Added `extract_playlist_id()` - Extract playlist ID from URL
   - Added `is_playlist_url()` - Check if URL is a playlist
   - Added `extract_playlist_videos()` - Fetch all videos from playlist

2. **`ai_tools/tools/youtube_agent.py`**
   - Added `sanitize_filename()` - Clean video titles for filenames
   - Added `save_to_markdown_file()` - Save content to .md file
   - Modified `run_youtube()` - Added `save_file` and `output_file` parameters
   - Added `run_youtube_batch()` - Process multiple videos with progress tracking

3. **`ai_tools/main.py`**
   - Changed `video` argument to `nargs="*"` for multiple inputs
   - Added `--save-file` flag for file saving
   - Added `-o/--output` flag for custom filename
   - Added logic to detect batch vs single video processing
   - Routes to appropriate function based on input

### Key Features

#### Filename Sanitization
- Removes invalid characters: `< > : " / \ | ? *`
- Replaces spaces with hyphens
- Truncates to 100 characters max
- Fallback to "untitled-video" if empty

#### Batch Processing Flow
1. Detect playlists and expand to video URLs
2. Process each video sequentially
3. Show progress bar with:
   - Current video number
   - Percentage complete
   - Estimated time remaining
4. Generate summary report with success/failure counts
5. List failed videos with error details

#### Error Handling
- Continues processing on individual video failures
- Tracks all errors for summary report
- Graceful handling of API rate limits
- Safe file operations with try/catch

## Validation & Error Handling

### Batch Mode Validation
When processing multiple videos or playlists, the `--save-file` flag is required. If you forget it, you'll see a clear error message:

```
⚠️  Batch Processing Requires File Output

You're trying to process multiple videos or a playlist.
Multiple analyses cannot be output to clipboard only.

Please add the --save-file flag:
  python ai_tools/main.py youtube URL1 URL2 ... --target markdown --save-file

This will save each video to a separate .md file in the current directory.
```

**Why this requirement?**
- Multiple video analyses cannot meaningfully fit in clipboard
- Console output would be overwhelming for multiple videos
- Files provide organized, persistent storage for batch results
- Makes user intent explicit (no accidental file creation)

**Auto-target selection:**
- When you use `--save-file`, markdown target is automatically selected
- If you specified `--target slack` with `--save-file`, it will override to markdown with a notification
- You'll see: `📄 Saving to markdown file(s)` or `📄 Using markdown target for file output (overriding --target slack)`
- This simplifies usage - just use `--save-file` and the right format is chosen

## Backward Compatibility

All existing functionality remains unchanged:
- Single video processing still works (clipboard only by default)
- Clipboard copy still happens (even with file save for single videos)
- Slack integration unchanged
- All existing flags work as before
- `--save-file` is optional for single videos, required for batch

## Requirements

No new dependencies required. Uses existing packages:
- `googleapiclient` - YouTube Data API (already used)
- `rich` - Progress bars and console output (already used)
- All other existing dependencies

## Configuration

Ensure `YOUTUBE_API_KEY` environment variable is set for:
- Playlist extraction
- Video title fetching

```bash
export YOUTUBE_API_KEY="your_youtube_api_key"
```

## Examples of Generated Files

### File naming examples:
- "How to Code in Python" → `How-to-Code-in-Python.md`
- "Machine Learning: A Deep Dive!" → `Machine-Learning-A-Deep-Dive.md`
- "Super Long Video Title That Goes On..." → `Super-Long-Video-Title-That-Goes-On-And-On-For-A-Very-Long-Time-But-Gets-Truncated-At-100.md`

### File content structure:
```markdown
# Video Title

*Introduction*
- Key objectives...

*Detailed Analysis*
1. Time-stamped section...

*Conclusion*
- Summary...
```

With `--dynamic-tags`:
```markdown
---
title: Video Title
tags:
  - tag1
  - tag2
  - tag3
---

(content follows...)
```

## Performance

- Single video: ~30-60 seconds (depends on transcript length and LLM)
- Batch processing: Sequential with 0.5s delay between videos
- Playlist extraction: <5 seconds for typical playlists

## Future Enhancements (Not Implemented)

Possible future additions:
- Parallel processing for multiple videos
- Resume capability (skip already processed videos)
- Custom output directory structure
- Combined output file option
- Input file with list of URLs
- Interactive video selection from playlist
