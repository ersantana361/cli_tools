# LeetCode Offline Editorial Reader

Extract and read LeetCode editorials offline from saved HTML pages.

## Quick Start

1. **Save a LeetCode problem page** (including editorial) as HTML from your browser
2. **Extract the editorial** to a clean Markdown file:
   ```bash
   python leetcode_offline.py your_saved_page.html
   ```
3. **Read offline** - the generated `.md` file contains the problem, examples, constraints, and editorial content

## Features

- ✅ **Clean formatting** - Converts HTML to readable Markdown
- ✅ **Offline reading** - No internet connection needed
- ✅ **Image download** - Automatically downloads and embeds problem diagrams/images
- ✅ **Complete content** - Problem description, examples, constraints, solution approach
- ✅ **Code templates** - Includes working solution code
- ✅ **Similar problems** - Lists related LeetCode problems

## Usage Examples

### Basic extraction
```bash
python leetcode_offline.py editorial.html
# Creates: editorial.md
```

### Custom output name
```bash
python leetcode_offline.py editorial.html -o binary_tree_traversal.md
```

### Extract and open immediately
```bash
python leetcode_offline.py editorial.html --view
```

### Skip image downloads (faster)
```bash
python leetcode_offline.py editorial.html --no-images
```

## Files Created

- **`extract_leetcode_editorial.py`** - Core extraction script
- **`leetcode_offline.py`** - User-friendly wrapper
- **Output `.md` file** - Clean, offline-readable editorial
- **`images/` directory** - Downloaded problem diagrams and illustrations

## How it Works

1. **Parses the HTML** saved from LeetCode
2. **Extracts JSON data** embedded in the page (`__NEXT_DATA__`)
3. **Downloads images** from LeetCode's CDN to local `images/` directory
4. **Converts to Markdown** with clean formatting and local image references
5. **Adds editorial content** including approach explanations and code templates

## Example Output Structure

```markdown
# LeetCode 102: Binary Tree Level Order Traversal

**Difficulty:** Medium
**Topics:** Tree, Breadth-First Search, Binary Tree

## Problem Description
[Clean problem statement]

## Examples
[Formatted input/output examples]

## Constraints
[Problem constraints]

## Editorial
[Approach explanations and solution code]

## Similar Questions
[Related problems list]
```

## Tips

- **Save complete page**: Make sure to save the HTML page after the editorial has loaded
- **Premium content**: Works with LeetCode Premium editorial content
- **Multiple formats**: Generated Markdown works with any Markdown viewer/editor
- **Version control friendly**: Clean text format works well with git

## Troubleshooting

- **"Could not extract JSON"**: The HTML file may not contain the editorial data
- **"Extraction failed"**: Check that the HTML file is complete and not corrupted
- **Formatting issues**: The script handles most HTML structures, but complex layouts may need manual cleanup

## Dependencies

- Python 3.6+
- Standard library only (no external packages required)

---
*Perfect for offline studying, note-taking, and building your own LeetCode problem collection!*