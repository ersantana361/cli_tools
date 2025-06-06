# CLI Utilities (PDF, YouTube, and GitHub)

This repository contains AI-powered CLI tools for document processing, GitHub PR analysis, YouTube content analysis, and structured Git workflows. The tools use an agentic, multi-step approach powered by smolagents, LangChain, and support multiple LLM providers (Anthropic Claude, DeepSeek).

## Main CLI Interface (`ai_tools`)

The primary interface is through `ai_tools/main.py`, which provides three main commands: `convert`, `github`, and `youtube`.

### Quick Setup with Aliases

For convenient usage, add these aliases to your `~/.bashrc` or `~/.zshrc`:

```bash
# Main AI Tools
alias ai_tools="python3 /home/ersantana/dev/scripts/cli_tools/ai_tools/main.py"
alias ngit="python3 /home/ersantana/dev/scripts/cli_tools/ngit/main.py"

# PDF Utilities
alias pdf_find="python3 /home/ersantana/dev/scripts/cli_tools/search_in_pdf.py"
alias pdf_read_page="python3 /home/ersantana/dev/scripts/cli_tools/read_page_in_pdf.py"
alias pdf_copy_content="python3 /home/ersantana/dev/scripts/cli_tools/copy_pdf_content.py"

# Code and Development Tools
alias rag_code="python3 /home/ersantana/dev/scripts/cli_tools/rag_code.py"
alias generate_prompt="python3 /home/ersantana/dev/scripts/cli_tools/generate_prompt.py"

# Data Processing
alias xml_to_json="python3 /home/ersantana/dev/scripts/cli_tools/xml_to_json.py"

# System Utilities
alias rename_tab="python3 /home/ersantana/dev/scripts/cli_tools/rename_tab.py"
```

Then reload your shell: `source ~/.bashrc`

**Usage Examples:**
```bash
# AI Tools (main interface)
ai_tools convert input.pdf --format enhanced --clipboard
ai_tools github https://github.com/owner/repo/pull/123 --target slack
ai_tools youtube "https://youtu.be/VIDEO_ID" --dynamic-tags --target markdown

# PDF Operations
pdf_find ./documents "keyword"
pdf_read_page document.pdf 5
pdf_copy_content document.pdf

# Structured Git Workflow
ngit
```

## Commands & Capabilities

### 1. PDF Conversion (`convert`)

Convert PDF files to Markdown with AI-powered formatting and content extraction.

**Usage:**
```bash
ai_tools convert <pdf_path_or_url> [options]
```

**Options:**
- `-o, --output`: Output file path (default: output.md)
- `--format`: Conversion format - `basic` or `enhanced` (default: basic)
- `--clipboard`: Copy result to clipboard
- `--verbose`: Enable detailed logging

**Examples:**
```bash
ai_tools convert document.pdf --format enhanced --clipboard
ai_tools convert https://example.com/paper.pdf -o research_notes.md
```

### 2. GitHub PR Analysis (`github`)

Generate comprehensive GitHub pull request analysis and reports.

**Usage:**
```bash
ai_tools github <pr_url> [options]
```

**Options:**
- `--target`: Output format - `github` or `slack` (default: github)
- `--llm-provider`: LLM provider - `anthropic` or `deepseek` (default: anthropic)

**Features:**
- Fetches and analyzes PR diffs
- Generates detailed, structured reports
- Security and performance analysis
- Multiple output formats for different platforms
- Option to update PR descriptions

**Examples:**
```bash
ai_tools github "https://github.com/owner/repo/pull/123" --target slack
ai_tools github "https://github.com/owner/repo/pull/456" --llm-provider anthropic
```

### 3. YouTube Video Analysis (`youtube`)

Analyze YouTube video content with transcript extraction and AI-powered insights.

**Usage:**
```bash
ai_tools youtube <video_url> [options]
```

**Options:**
- `--target`: Output format - `markdown` or `slack` (required)
- `--language`: Transcript language code (default: en)
- `--slack-thread`: Slack thread URL (required for slack target)
- `--prompt-only`: Generate prompt without LLM analysis
- `--dynamic-tags`: Generate dynamic content tags (markdown only)
- `--llm-provider`: LLM provider - `anthropic` or `deepseek` (default: anthropic)

**Features:**
- Transcript extraction and formatting
- Chronological content breakdown
- Dynamic tag generation
- Multi-language support
- Slack integration with thread posting

**Examples:**
```bash
ai_tools youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --target markdown --dynamic-tags
ai_tools youtube "https://youtu.be/VIDEO_ID" --target slack --slack-thread "https://slack.com/archives/CHANNEL/pTIMESTAMP"
```

## Additional Utilities

### PDF Tools

**`pdf_read_page`** - Extract text from specific PDF pages:
```bash
pdf_read_page myfile.pdf 2
```

**`pdf_find`** - Search PDFs in directory for keywords:
```bash
pdf_find ./documents "CQRS"
```

**`pdf_copy_content`** - Copy PDF content with formatting:
```bash
pdf_copy_content document.pdf
```

### Code & Development Tools

**`rag_code`** - RAG-based code analysis:
```bash
rag_code
```

**`generate_prompt`** - Generate AI prompts for code:
```bash
generate_prompt
```

### Data Processing Tools

**`xml_to_json`** - Convert XML files to JSON:
```bash
xml_to_json input.xml
```

### System Utilities

**`rename_tab`** - Rename terminal tabs:
```bash
rename_tab "New Tab Name"
```

## Other Tools in Repository

### PR Review Tools (`pr_reviewer/`)
- Modular PR review package with object-oriented design
- Security-focused reviews with performance analysis
- Direct integration with GitHub API

### MCP Integration (`mcp/`)
- Model Context Protocol integration for Claude Desktop
- Direct Claude CLI integration for PR reviews

### Structured Git Workflows (`ngit/`)
- Implements Kent Beck's "Tidy First?" philosophy
- AI-powered commit categorization with automatic backups
- Separates structural from behavioral changes

## Setup and Installation

### 1. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Your Aliases (Recommended)

Add all the convenient aliases to your `~/.bashrc` or `~/.zshrc` (see the alias section above for the complete list).

Then reload your shell:
```bash
source ~/.bashrc
```

## Environment Variables

Create a `.env` file or set environment variables:

- **ANTHROPIC_API_KEY:** API key for Claude LLM
- **DEEPSEEK_API_KEY:** API key for DeepSeek LLM (alternative provider)
- **GITHUB_TOKEN_WORK:** Token for accessing GitHub repositories
- **YOUTUBE_API_KEY:** API key for YouTube Data API
- **SLACK_TOKEN:** Token for Slack integration

## Key Features

- **Multi-Provider LLM Support:** Switch between Anthropic Claude and DeepSeek
- **Rich CLI Interface:** Enhanced console output with progress bars and formatting
- **Agent-Based Architecture:** Uses LangChain and SmolaAgents for complex workflows
- **Multiple Output Formats:** GitHub Markdown, Slack formatting, clipboard integration
- **Security & Safety:** Automatic backups, dry-run modes, comprehensive error handling
