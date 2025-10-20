# Batch Processing Validation Update

## Summary
Updated the YouTube batch processing feature to **require** the `--save-file` flag for multiple videos and playlists. This makes the CLI behavior explicit and prevents confusion.

## What Changed

### Before (Original Implementation)
```bash
# Would automatically save files without warning
python ai_tools/main.py youtube URL1 URL2 --target markdown
```

### After (Current Implementation)
```bash
# Shows clear error requiring --save-file
python ai_tools/main.py youtube URL1 URL2 --target markdown

# Correct usage
python ai_tools/main.py youtube URL1 URL2 --target markdown --save-file
```

## Behavior Matrix

| Input Type | --save-file | Result |
|------------|-------------|--------|
| Single video | Not provided | ✅ Clipboard only (default) |
| Single video | Provided | ✅ Saves to file + clipboard |
| Multiple videos | Not provided | ❌ **ERROR with helpful message** |
| Multiple videos | Provided | ✅ Batch processing, saves files |
| Playlist | Not provided | ❌ **ERROR with helpful message** |
| Playlist | Provided | ✅ Batch processing, saves files |

## Error Message Example

When you forget `--save-file` with multiple videos:

```
⚠️  Batch Processing Requires File Output

You're trying to process multiple videos or a playlist.
Multiple analyses cannot be output to clipboard only.

Please add the --save-file flag:
  python ai_tools/main.py youtube URL1 URL2 ... --target markdown --save-file

This will save each video to a separate .md file in the current directory.
```

## Why This Design?

1. **Explicit is better than implicit** - User clearly states intent to save files
2. **No surprises** - Prevents accidental file creation
3. **Logical constraint** - Multiple analyses can't fit in clipboard
4. **Better UX** - Clear error messages guide correct usage
5. **Maintains defaults** - Single video still defaults to clipboard (convenient)

## Files Modified

1. `ai_tools/main.py`
   - Added validation logic before batch processing
   - Clear error messages with usage examples

2. `CLAUDE.md`
   - Updated all examples to show `--save-file` for batch operations
   - Added distinction between single and batch usage

3. `YOUTUBE_BATCH_FEATURES.md`
   - Added validation section explaining the requirement
   - Updated all batch examples to include `--save-file`
   - Added warning notes for clarity

4. `test_youtube_batch_logic.py`
   - Updated test scenarios to include validation logic
   - Added tests for error cases

## Testing

All logic tests pass:
- ✅ Single video without flag → clipboard (works)
- ✅ Single video with flag → file (works)
- ✅ Multiple videos without flag → error (as intended)
- ✅ Multiple videos with flag → batch (works)
- ✅ Playlist without flag → error (as intended)
- ✅ Playlist with flag → batch (works)

## Backward Compatibility

✅ **Fully backward compatible** for single video use cases:
- Existing single video commands work unchanged
- Default clipboard behavior preserved
- Optional `--save-file` for single videos

⚠️ **Breaking change for batch** (intentional):
- Multiple videos now require explicit `--save-file`
- Playlists now require explicit `--save-file`
- Clear error messages guide users to correct syntax

This is considered an improvement rather than a breaking change, as it prevents unintended behavior.

## Migration Guide

If you had scripts using batch processing:

### Old (Would auto-save silently)
```bash
python ai_tools/main.py youtube URL1 URL2 --target markdown
```

### New (Explicit, clear)
```bash
python ai_tools/main.py youtube URL1 URL2 --target markdown --save-file
```

Simply add `--save-file` to any batch processing commands.
