# PDF Utilities

This repository contains two Python scripts for working with PDF files using `pdfminer`. These scripts allow you to extract text from a specific page in a PDF or search for a keyword within all PDF files in a directory, extracting the paragraph containing the keyword.

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

## Dependencies

### Installation

To install the necessary dependencies, run:
```bash
pip install -r requirements.txt
```
