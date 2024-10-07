
# PDF and YouTube Utilities

This repository contains Python scripts for working with PDF files and YouTube video transcripts. You can extract text from a specific page in a PDF, search for a keyword within all PDF files in a directory, or copy the transcript of a YouTube video to your clipboard.

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
This script fetches the transcript of a YouTube video and copies it to your clipboard.

#### Usage:
```bash
python youtube_transcript.py <video_id_or_url>
```

#### Arguments:
- `<video_id_or_url>`: The ID or URL of the YouTube video.

#### Example:
```bash
python youtube_transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### Features:
- Extracts the text transcript of a YouTube video.
- Copies the transcript directly to your clipboard for easy use.

## Dependencies

### Installation

To install the necessary dependencies, run:
```bash
pip install -r requirements.txt
```
