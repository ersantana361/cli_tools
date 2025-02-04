import argparse
import pyperclip
from pdfminer.high_level import extract_text

def extract_pdf_text(pdf_path):
    try:
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        print(f"Error processing PDF: {pdf_path} - {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from a PDF and copy it to the clipboard")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()

    pdf_text = extract_pdf_text(args.pdf_path)
    if pdf_text:
        pyperclip.copy(pdf_text)
        print("PDF text copied to clipboard successfully!")
    else:
        print("Failed to extract text from the PDF.")

