#!/usr/bin/env python3
import re
import argparse
from pathlib import Path

# Map file extensions to Markdown language tags
# User-specified: .py, .json, .tsx, .ts, .yml
EXTENSION_TO_LANGUAGE = {
    '.py': 'python',
    '.json': 'json',
    '.tsx': 'typescript',  # tsx is a superset of typescript
    '.ts': 'typescript',
    '.yml': 'yaml',
    '.yaml': 'yaml',      # Common alternative for YAML files
    # You can add more mappings here as needed, e.g.:
    # '.js': 'javascript',
    # '.html': 'html',
    # '.css': 'css',
    # '.md': 'markdown',
    # '.java': 'java',
    # '.cs': 'csharp',
    # '.cpp': 'cpp',
    # '.c': 'c',
    # '.sh': 'bash',
    # '.rb': 'ruby',
}

def generate_prompt(base_prompt=None, no_copy=False):
    """Process prompts with {{filename}} placeholders from various sources"""
    try:
        import pyperclip
    except ImportError:
        pyperclip = None

    # Get base prompt
    if base_prompt is None:
        if not pyperclip:
            raise RuntimeError("pyperclip required for clipboard operations")
        base_prompt = pyperclip.paste()
        print("ℹ Using prompt from clipboard")
        if not base_prompt.strip():
            raise ValueError("Clipboard is empty or contains only whitespace")

    # Find unique file paths
    placeholders = re.findall(r'\{\{(.+?)\}\}', base_prompt)
    unique_files = list(set(placeholders))
    print(f"\n🔍 Found {len(unique_files)} unique file references to process:")

    # Read files with detailed feedback
    file_contents = {}
    missing_files = []
    for idx, file_path_str in enumerate(unique_files, 1):
        print(f"  {idx}. {file_path_str}: ", end="", flush=True)
        try:
            path_obj = Path(file_path_str)
            with open(path_obj, 'r', encoding='utf-8') as f:
                file_contents[file_path_str] = f.read()
            print("✓ Found ({} chars)".format(len(file_contents[file_path_str])))
        except FileNotFoundError:
            print("✗ Not found")
            missing_files.append(file_path_str)
        except Exception as e:
            print(f"⚠ Error: {str(e)}")
            missing_files.append(file_path_str)

    # Check for missing files
    if missing_files:
        print("\n❌ Missing files:")
        for f in missing_files:
            print(f"  - {f}")
        raise RuntimeError(f"Missing {len(missing_files)} required files")

    # Helper function to format the replacement
    def format_replacement(match):
        file_path_placeholder = match.group(1) # e.g., "tests/test_handle_scene_types.py"
        actual_file_content = file_contents[file_path_placeholder]
        
        # Determine the language for syntax highlighting
        file_extension = Path(file_path_placeholder).suffix.lower() # e.g., ".py"
        language_tag = EXTENSION_TO_LANGUAGE.get(file_extension, '') # Get lang or empty string
        
        # Construct the replacement string with the filename, language-tagged code block, and content
        return f"{file_path_placeholder}\n```{language_tag}\n{actual_file_content}\n```"

    # Replace placeholders
    completed_prompt = re.sub(
        r'\{\{(.+?)\}\}',
        format_replacement,
        base_prompt
    )

    # Write to output file
    try:
        with open('prompt_output.txt', 'w', encoding='utf-8') as f:
            f.write(completed_prompt)
        print(f"\n✓ Prompt saved to 'prompt_output.txt' ({len(completed_prompt)} characters)")
    except Exception as e:
        print(f"\n⚠ File write failed: {str(e)}")

    # Handle clipboard
    if not no_copy and pyperclip:
        try:
            pyperclip.copy(completed_prompt)
            print("✓ Prompt copied to clipboard")
        except Exception as e:
            print(f"⚠ Clipboard copy failed: {str(e)}")
    else:
        print("ℹ Clipboard copy skipped (--no-copy specified)" if no_copy else "ℹ pyperclip not installed, skipping copy.")

    return completed_prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate prompts with file contents, adding language tags for Markdown. Output is copied to clipboard and saved to prompt_output.txt',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-p', '--prompt', help='Direct prompt input string')
    parser.add_argument('-f', '--file', type=Path,
                        help='Path to a file containing the prompt')
    parser.add_argument('--no-copy', action='store_true',
                        help='Disable copying the generated prompt to the clipboard')

    args = parser.parse_args()

    if args.prompt and args.file:
        parser.error("Specify only one input method: --prompt (-p) or --file (-f), not both.")

    input_prompt_source_message = ""
    base_prompt_content = None # Renamed from base_prompt to avoid confusion in this scope

    if args.file:
        if not args.file.exists():
            print(f"\n❌ Error: Prompt file {args.file} not found.")
            exit(1)
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                base_prompt_content = f.read()
            input_prompt_source_message = f"ℹ Using prompt from file: {args.file}"
        except Exception as e:
            print(f"\n❌ Error reading prompt file {args.file}: {str(e)}")
            exit(1)
    elif args.prompt:
        base_prompt_content = args.prompt
        input_prompt_source_message = "ℹ Using prompt from command line argument."
    # If neither -p nor -f is provided, base_prompt_content remains None,
    # and generate_prompt will attempt to use the clipboard.

    if input_prompt_source_message:
         print(input_prompt_source_message)

    try:
        generate_prompt(base_prompt_content, args.no_copy)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)