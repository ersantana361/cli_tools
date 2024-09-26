import argparse
from pdfminer.high_level import extract_text

def extract_page_text(pdf_path, page_num):
    try:
        text = extract_text(pdf_path, page_numbers=[page_num - 1])
        return text
    except Exception as e:
        print(f"Error processing PDF: {pdf_path} - {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from a PDF page")
    parser.add_argument("pdf_text", help="Path to the PDF file")
    parser.add_argument("page_num", type=int, help="Page number to extract")
    args = parser.parse_args()

    page_text = extract_page_text(args.pdf_text, args.page_num)
    if page_text:
        print(page_text)
    else:
        print("Failed to extract text from the specified page.")
