import logging
from pdfminer.high_level import extract_text
from pdfminer.pdfpage import PDFPage
import os
import argparse
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

def extract_full_paragraph(text, keyword):
    keyword_index = text.find(keyword)
    if keyword_index == -1:
        return None

    paragraph_start = text.rfind("\n\n", 0, keyword_index)
    if paragraph_start == -1:
        paragraph_start = 0

    paragraph_end = text.find("\n\n", keyword_index)
    if paragraph_end == -1:
        paragraph_end = len(text)

    return text[paragraph_start:paragraph_end].strip()

def search_pdfs_recursively(directory, keyword):
    findings = []
    processed_files = 0
    missing_files = 0
    total_files = sum(1 for _, _, files in os.walk(directory) for file in files if file.endswith(".pdf"))
    
    with tqdm(total=total_files) as pbar:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    processed_files += 1

                    try:
                        with open(pdf_path, 'rb') as f:
                            page_num = 0
                            for _ in PDFPage.get_pages(f):
                                page_num += 1
                                page_text = extract_text(pdf_path, page_numbers=[page_num - 1])

                                if keyword in page_text:
                                    context = extract_full_paragraph(page_text, keyword)

                                    if context:
                                        findings.append((pdf_path, page_num, context))

                    except Exception as e:
                        logging.error(f"Error processing PDF: {pdf_path} - {e}")
                        missing_files += 1

                    pbar.update(1)

    index = 0
    print("\n- Findings -")
    if len(findings) == 0:
        print("\nFindings: None")
    for finding in findings:
        if index > 0:
            print('\n')
        index += 1
        print(f"- Found: '{keyword}' on page {finding[1]}\n- file: {finding[0]}\n- content:\n{finding[2]}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for a keyword in PDFs within a directory")
    parser.add_argument("directory", help="Directory to search (use '.' for current directory)")
    parser.add_argument("keyword", help="Keyword to search for")
    
    args = parser.parse_args()
    directory = os.path.abspath(args.directory)
    search_pdfs_recursively(directory, args.keyword)

