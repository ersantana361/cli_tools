# Auto-Markdown Target Update

## Summary
Simplified YouTube CLI by automatically using markdown target when `--save-file` is specified, with clear user notifications.

## What Changed

### Before
```bash
# User had to specify both --target and --save-file
python ai_tools/main.py youtube "URL" --target markdown --save-file
```

### After
```bash
# --target markdown is automatic, just use --save-file
python ai_tools/main.py youtube "URL" --save-file
# Output: 📄 Saving to markdown file(s)
```

## New Behavior

### Automatic Target Selection
When `--save-file` is used:
1. Automatically sets target to "markdown"
2. Shows notification: `📄 Saving to markdown file(s)`
3. Overrides conflicting `--target slack` if specified

### User Notifications

**Scenario 1: Using --save-file without explicit target**
```bash
$ python ai_tools/main.py youtube "URL" --save-file
📄 Saving to markdown file(s)
```

**Scenario 2: Using --save-file with --target slack (conflict)**
```bash
$ python ai_tools/main.py youtube "URL" --save-file --target slack
📄 Using markdown target for file output (overriding --target slack)
```

**Scenario 3: Using --save-file with explicit --target markdown**
```bash
$ python ai_tools/main.py youtube "URL" --save-file --target markdown
📄 Saving to markdown file(s)
```

**Scenario 4: No --save-file (default)**
```bash
$ python ai_tools/main.py youtube "URL"
# (No notification, uses clipboard)
```

## Updated Usage Examples

### Simplified Commands

**Single video with file save:**
```bash
# Before
python ai_tools/main.py youtube "URL" --target markdown --save-file

# After (simpler!)
python ai_tools/main.py youtube "URL" --save-file
```

**Multiple videos:**
```bash
# Before
python ai_tools/main.py youtube "URL1" "URL2" --target markdown --save-file

# After (simpler!)
python ai_tools/main.py youtube "URL1" "URL2" --save-file
```

**Playlist:**
```bash
# Before
python ai_tools/main.py youtube "PLAYLIST_URL" --target markdown --save-file

# After (simpler!)
python ai_tools/main.py youtube "PLAYLIST_URL" --save-file
```

## Rationale

1. **Less typing** - Don't need to specify `--target markdown` when saving files
2. **Logical consistency** - File saving only makes sense with markdown format
3. **Prevents errors** - Can't accidentally try to save Slack-formatted output to files
4. **Clear feedback** - User sees exactly what's happening with notification messages
5. **Simpler mental model** - "I want to save files? Just use --save-file"

## Implementation Details

### Changes Made

**1. CLI Argument (`main.py`)**
- Made `--target` optional (removed `required=True`)
- Default value remains "markdown"
- Updated help text to mention auto-selection

**2. Auto-detection Logic (`main.py`)**
```python
if args.save_file:
    if args.target == "slack":
        console.print("[cyan]📄 Using markdown target for file output (overriding --target slack)[/cyan]")
        args.target = "markdown"
    else:
        console.print("[cyan]📄 Saving to markdown file(s)[/cyan]")
```

**3. Documentation Updates**
- `CLAUDE.md` - Removed `--target markdown` from all file-saving examples
- `YOUTUBE_BATCH_FEATURES.md` - Updated examples and added explanation
- All examples now show the simpler `--save-file` only syntax

## Behavior Matrix

| Flags Used | Target Result | Notification |
|------------|---------------|--------------|
| (none) | markdown | None (clipboard mode) |
| `--save-file` | markdown (auto) | "📄 Saving to markdown file(s)" |
| `--target slack` | slack | None |
| `--save-file --target slack` | markdown (override) | "📄 Using markdown target for file output (overriding --target slack)" |
| `--save-file --target markdown` | markdown | "📄 Saving to markdown file(s)" |

## Backward Compatibility

✅ **Fully backward compatible:**
- Old commands with `--target markdown --save-file` still work
- Just shows the same notification message
- No breaking changes to any functionality

## Testing

All scenarios verified:
- ✅ Default behavior (no flags) → clipboard
- ✅ `--save-file` alone → markdown auto-selected with notification
- ✅ `--save-file --target slack` → overridden with notification
- ✅ `--save-file --target markdown` → explicit choice with notification
- ✅ Batch processing with `--save-file` → works correctly

## Benefits Summary

**For Users:**
- 🎯 Less typing (fewer flags to remember)
- 💡 Clear feedback (knows what's happening)
- 🚫 Prevents mistakes (can't save with wrong format)
- 📚 Simpler documentation (easier to learn)

**For Maintainability:**
- 🧹 Cleaner code (less redundant flag combinations)
- 📖 Easier to explain (simpler mental model)
- 🐛 Fewer edge cases (format is always correct for file saving)
