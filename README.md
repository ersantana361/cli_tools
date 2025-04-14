# CLI Utilities (PDF, YouTube and Github)

This repository contains Python scripts for working with PDF files, YouTube video transcripts, and GitHub pull request descriptions. You can extract text from a specific page in a PDF, search for keywords within all PDF files in a directory, copy YouTube video transcripts, and even generate formatted GitHub PR reports using interactive prompts.

## Scripts

### 1. `read_page_in_pdf.py`
This script extracts text from a specific page of a PDF file.

#### Usage:
```bash
python read_page_in_pdf.py <pdf_file_path> <page_number>
```

#### Arguments:
- `<pdf_file_path>`: The path to the PDF file.
- `<page_number>`: The page number to extract (1-based index).

#### Example:
```bash
python read_page_in_pdf.py myfile.pdf 2
```

### 2. `search_in_pdf.py`
This script recursively searches through all PDF files in a given directory for a specific keyword and extracts the paragraph containing the keyword.

#### Usage:
```bash
python search_in_pdf.py <directory> <keyword>
```

#### Arguments:
- `<directory>`: The directory to search (use `.` for the current directory).
- `<keyword>`: The keyword to search for within the PDF files.

#### Example:
```bash
python search_in_pdf.py ./documents "CQRS"
```

#### Features:
- Recursively searches all PDFs in the specified directory.
- Extracts the paragraph surrounding the keyword.
- Displays the page number and the extracted paragraph for each occurrence.

### 3. `youtube_transcript.py`
This script fetches the transcript of a YouTube video and generates a detailed video transcript analysis using LangChain and Deepseek. It offers options to run in prompt-only mode (which generates only the analysis prompt without invoking the LLM) or to obtain the full analysis result. When using Markdown output, you can choose between generating dynamic tags (based on the analysis output) or using static tags. The final output—including YAML metadata—is copied to your clipboard and displayed using Rich's Markdown rendering.

#### Usage:
```bash
python youtube_transcript.py <video_id_or_url> [--language <lang_code>] [--target markdown|slack] [--prompt-only] [--dynamic-tags]
```

#### Arguments:
- `<video_id_or_url>`: The ID or URL of the YouTube video.
- `--language`: Language code for the transcript (default: en).
- `--target`: Output format option (markdown (default) or slack).
- `--prompt-only`: If set, only generate the prompt without invoking the LLM.
- `--dynamic-tags`: If set, generate dynamic tags based on the analysis output; if not set, static tags will be used.

#### Example:
```bash
python youtube_transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --dynamic-tags
```

#### Features:
- Extracts the transcript from a YouTube video.
- Generates and sends an analysis prompt to an LLM via LangChain.
- Offers comprehensive analysis options including dynamic tag generation.
- Supports both Markdown and Slack output formats.
- Copies the final result to your clipboard and pretty-prints it in the terminal.

### 4. `github_desc.py`
This script generates a formatted pull request (PR) report by fetching the diff from a GitHub PR, analyzing it with Deepseek, and then creating a detailed report using LangChain. The report can be formatted for GitHub (Markdown) or Slack, and the final output is automatically copied to your clipboard. Interactive prompts (using Questionary) ask if you want to update the PR description.

#### Usage:
```bash
python github_desc.py <pr_link> [--target github|slack]
```

#### Arguments:
- `<pr_link>`: The GitHub pull request URL.
- `--target`: Output format option (github (default) or slack).

#### Example:
```bash
python github_desc.py "https://github.com/owner/repo/pull/123" --target slack
```

#### Features:
- Fetches the diff (patch) from a private GitHub repository.
- Analyzes the code changes using Deepseek.
- Generates a detailed PR report with structured sections.
- Supports both GitHub Markdown and Slack formatting.
- Uses interactive prompts to confirm if the PR description should be updated.
- Copies the final report to your clipboard for easy sharing.

## Setup and Installation

It is recommended to use a virtual environment for this project to avoid conflicts with other Python packages on your system.

### Setting Up a Virtual Environment

1. **Create a Virtual Environment:**

   ```bash
   python -m venv cli-tools-env
   ```

2. **Activate the Virtual Environment:**
   - On **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```
   - On **Windows**:
     ```bash
     venv\Scripts\activate
     ```

3. **Install the Required Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Requirements

This project uses a `requirements.txt` file to manage dependencies. The dependencies are pinned to specific versions to avoid conflicts (especially for smolagents and its related packages).
