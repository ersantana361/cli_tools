Here's the proper README content without markdown code block wrapping:

# ToolSuite: Unified Document, GitHub, and YouTube Analysis Toolkit  

A command-line toolkit combining document conversion, GitHub PR analysis, and YouTube transcript processing with LLM-powered insights.

## Features  

**PDF Conversion**  
- Convert PDFs to formatted Markdown  
- Local files and URL support  
- Enhanced formatting options  
- Clipboard integration  
- Progress tracking  

**GitHub Analysis**  
- Generate PR reports (GitHub/Slack formats)  
- Automatic diff analysis  
- PR description updating  
- LLM-powered code insights  

**YouTube Processing**  
- Transcript extraction & analysis  
- Video content breakdown  
- Dynamic tag generation  
- Multi-format output (Markdown/Slack)  

## Installation  

1. Clone repository:  
`git clone https://github.com/ersantana361/cli_tools.git`  
2. Install dependencies:  
`pip install -r requirements.txt`  

## Configuration  

Set environment variables in your shell profile:  

```bash
# Deepseek API key for LLM features
export DEEPSEEK_API_KEY="your_api_key"

# GitHub token for private repo access
export GITHUB_TOKEN_WORK="your_github_token"
```

## Usage  

```
python main.py <command> [options]

Commands:
  convert    Convert PDF documents to Markdown
  github     Analyze GitHub pull requests
  youtube    Analyze YouTube transcripts

Run 'python main.py <command> -h' for detailed help
```

### PDF Conversion Command  

```bash
python main.py convert input.pdf --format enhanced --clipboard --verbose
```

**Key Options**:
- `input_source`: PDF path/URL (required)
- `-o/--output`: Output file (default: output.md)
- `--format`: basic/enhanced formatting
- `--clipboard`: Copy to system clipboard

### GitHub Analysis Command  

```bash
python main.py github https://github.com/owner/repo/pull/123 --target slack
```

**Key Options**:
- `pr_link`: Full GitHub PR URL (required)
- `--target`: Output format (github|slack)

### YouTube Analysis Command  

```bash
python main.py youtube "https://youtu.be/VIDEO_ID" --dynamic-tags --target markdown
```

**Key Options**:
- `video`: YouTube URL/ID (required)
- `--language`: Transcript language (default: en)
- `--dynamic-tags`: Generate content-based tags
- `--prompt-only`: Output analysis prompt without LLM processing

## Examples  

**Convert PDF from URL**  
```bash
python main.py convert "https://example.com/doc.pdf" -o report.md --format enhanced
```

**Analyze Private GitHub PR**  
```bash
python main.py github https://github.com/yourorg/private-repo/pull/42 --target slack
```

**Generate YouTube Analysis with Tags**  
```bash
python main.py youtube "https://youtu.be/abc123" --dynamic-tags --target markdown
```

## Troubleshooting  

**Common Issues**:  
- Missing API Keys: Verify both DEEPSEEK_API_KEY and GITHUB_TOKEN_WORK are set  
- Invalid PR Format: Use full GitHub URL (e.g., https://github.com/owner/repo/pull/123)  
- Transcript Errors: Ensure video has captions enabled  

**Verbose Debugging**:  
Add `--verbose` flag to commands for detailed error output:  
```bash
python main.py convert input.pdf --verbose
```

## License  

MIT License - See [LICENSE](LICENSE) for full text.  

This format maintains proper markdown syntax while containing code examples and structure blocks without premature closure issues.
