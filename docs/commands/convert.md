# convert Command

[Home](../README.md) > [Commands](README.md) > convert

Convert PDF documents to Markdown format.

## Usage

```bash
ai convert INPUT [options]
```

## Examples

### Basic Conversion

```bash
ai convert document.pdf
```

Converts PDF and saves to `output.md`.

### Enhanced Formatting

```bash
ai convert document.pdf --format enhanced
```

Uses AI to improve formatting and structure.

### Copy to Clipboard

```bash
ai convert document.pdf --clipboard
```

Copies the converted markdown to clipboard.

### Custom Output File

```bash
ai convert document.pdf -o my-document.md
```

### From URL

```bash
ai convert "https://example.com/document.pdf" --format enhanced
```

### Full Example

```bash
ai convert report.pdf --format enhanced --clipboard -o report.md
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output file path | `output.md` |
| `--format` | Format mode (`basic`/`enhanced`) | `basic` |
| `--clipboard` | Copy result to clipboard | disabled |
| `--verbose` | Show detailed progress | disabled |

## Format Modes

### Basic Mode

Simple extraction of text from PDF:

```bash
ai convert document.pdf --format basic
```

- Fast processing
- Preserves original structure
- No AI enhancement

### Enhanced Mode

AI-improved formatting:

```bash
ai convert document.pdf --format enhanced
```

- Better heading detection
- Improved list formatting
- Table structure preservation
- Cleaner output

## Input Sources

### Local Files

```bash
ai convert ./documents/report.pdf
ai convert ~/Downloads/paper.pdf
```

### URLs

```bash
ai convert "https://example.com/whitepaper.pdf"
```

The PDF is downloaded and processed locally.

## Output

The generated markdown preserves:

- Headings and subheadings
- Paragraphs and text flow
- Lists (bulleted and numbered)
- Tables (when detectable)
- Basic formatting (bold, italic)

## Troubleshooting

### "File not found"

Make sure the path is correct:

```bash
# Check if file exists
ls -la document.pdf

# Use absolute path if needed
ai convert /full/path/to/document.pdf
```

### Poor formatting

Try enhanced mode:

```bash
ai convert document.pdf --format enhanced
```

### Large files

Large PDFs may take longer to process. Use `--verbose` to see progress:

```bash
ai convert large-document.pdf --verbose
```

## Related

- [Quick Start](../getting-started/quick-start.md) - First commands
- [Commands Reference](README.md) - All commands
