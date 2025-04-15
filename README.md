# CLI Utilities (PDF, YouTube, and GitHub)

This repository contains Python scripts that let you work with PDF files, YouTube video transcripts, and GitHub pull request descriptions using an agentic, multi-step approach powered by smolagents, LangChain, and Deepseek. You can extract text from specific pages in PDFs, search for keywords in PDFs throughout a directory, obtain detailed YouTube video analyses (including dynamic tag generation), and generate formatted GitHub PR reports—with the option to automatically update PR descriptions.

## Scripts & Capabilities

### 1. PDF Utilities

**a. `read_page_in_pdf.py`**  
Extracts text from a specified page of a PDF file.

**Usage:**
```bash
python read_page_in_pdf.py <pdf_file_path> <page_number>
```

**Example:**
```bash
python read_page_in_pdf.py myfile.pdf 2
```

**b. `search_in_pdf.py`**  
Recursively searches PDF files in a directory for a keyword and extracts the surrounding paragraph.

**Usage:**
```bash
python search_in_pdf.py <directory> <keyword>
```

**Example:**
```bash
python search_in_pdf.py ./documents "CQRS"
```

### 2. Unified Agent for GitHub and YouTube

The `main.py` script now serves as a unified command-line interface with subcommands.

**a. GitHub Agent**

Generate a formatted GitHub pull request (PR) report by:

- Fetching the diff from a GitHub PR.
- Analyzing code changes via Deepseek.
- Generating a detailed, structured report (in GitHub Markdown or Slack style).
- Displaying the current PR description and optionally updating it.

**Usage:**
```bash
python main.py github <pr_link> [--target github|slack]
```

**Example:**
```bash
python main.py github "https://github.com/owner/repo/pull/123" --target slack
```

**b. YouTube Agent**

Analyze a YouTube video transcript by:

- Extracting the video ID and fetching its title.
- Retrieving and formatting the transcript.
- Creating and sending an analysis prompt to an LLM to generate a detailed breakdown.
- Optionally generating dynamic tags for Markdown output.
- Copying the final result to your clipboard and displaying it using Rich.

**Usage:**
```bash
python main.py youtube <video_id_or_url> [--language <lang_code>] [--target markdown|slack] [--prompt-only] [--dynamic-tags]
```

**Example:**
```bash
python main.py youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --dynamic-tags
```

## Features

- **PDF Utilities:**
  - Extract specific pages.
  - Perform keyword searches with context extraction.
  
- **GitHub Agent:**
  - Automatically fetch and analyze GitHub PR diffs.
  - Generate detailed, formatted reports in multiple output styles.
  - Display the current PR description and update it via interactive prompts.
  - Copy the generated report to your clipboard for easy sharing.
  
- **YouTube Agent:**
  - Fetch video transcripts and video metadata.
  - Generate in-depth transcript analysis with a chronological breakdown.
  - Option for dynamic tag generation for Markdown reports.
  - Offers a "prompt-only" mode to preview the generated prompt.
  - Copies the final result to your clipboard and renders it using Rich.

## Setup and Installation

### 1. Create and Activate a Virtual Environment

Create a virtual environment:
```bash
python -m venv venv
```

Activate the virtual environment:

- On **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```
- On **Windows**:
  ```bash
  venv\Scripts\activate
  ```

### 2. Install Dependencies

Install the required packages:
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file (or set environment variables) with the following keys:

- **DEEPSEEK_API_KEY:** API key for Deepseek/ChatOpenAI.
- **GITHUB_TOKEN_WORK:** Token for accessing private GitHub repositories.
- **YOUTUBE_API_KEY:** API key for the YouTube Data API.

## Usage Examples

### Generate a GitHub PR Report:
```bash
python main.py github "https://github.com/owner/repo/pull/123" --target github
```

### Analyze a YouTube Video with Dynamic Tags:
```bash
python main.py youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --dynamic-tags
```
