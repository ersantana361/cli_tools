import argparse
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())

def get_markdown_content(input_file):
    converter = DocumentConverter()
    result = converter.convert(input_file)
    return result.document.export_to_markdown()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a PDF file (or URL) to Markdown using DocumentConverter."
    )
    parser.add_argument(
        "input_file",
        help="Path or URL to the input PDF file."
    )
    parser.add_argument(
        "-o", "--output",
        default="output.md",
        help="Name of the output markdown file (default: output.md)"
    )
    return parser.parse_args()

def write_file(markdown_content, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

def main():
    args = parse_args()
    markdown_content = get_markdown_content(args.input_file)
    print("Converting files, it might take a couple of minutes")
    write_file(markdown_content, args.output)
    print(f"Markdown content has been saved to {args.output}")

if __name__ == "__main__":
    main()

