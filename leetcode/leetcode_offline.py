#!/usr/bin/env python3
"""
LeetCode Offline Reader

A simple wrapper script that extracts LeetCode editorials and provides
a clean offline reading experience.

Usage:
    python leetcode_offline.py editorial.html
    python leetcode_offline.py editorial.html --view
    python leetcode_offline.py editorial.html --output custom_name.md
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Extract and view LeetCode editorials offline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python leetcode_offline.py editorial.html              # Extract to editorial.md
  python leetcode_offline.py editorial.html --view       # Extract and open
  python leetcode_offline.py editorial.html -o custom.md # Custom output name
        """
    )

    parser.add_argument('html_file',
                       help='Path to the saved LeetCode HTML file')
    parser.add_argument('-o', '--output',
                       help='Output markdown file (default: based on input name)')
    parser.add_argument('--view', action='store_true',
                       help='Open the extracted markdown file after creation')
    parser.add_argument('--browser', action='store_true',
                       help='Open in browser instead of default editor')
    parser.add_argument('--no-images', action='store_true',
                       help='Skip downloading images')

    args = parser.parse_args()

    # Check if HTML file exists
    html_file = Path(args.html_file)
    if not html_file.exists():
        print(f"❌ Error: File {html_file} not found")
        sys.exit(1)

    # Extract the editorial
    extract_script = Path(__file__).parent / 'extract_leetcode_editorial.py'
    if not extract_script.exists():
        print(f"❌ Error: Extract script not found at {extract_script}")
        sys.exit(1)

    # Build extraction command
    cmd = ['python', str(extract_script), str(html_file)]
    if args.output:
        cmd.extend(['-o', args.output])
        output_file = Path(args.output)
    else:
        output_file = html_file.with_suffix('.md')

    # Run extraction
    try:
        if args.no_images:
            print(f"📄 Extracting editorial from {html_file.name} (without images)...")
        else:
            print(f"📄 Extracting editorial from {html_file.name} (with images)...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Extraction failed:")
            print(result.stderr)
            sys.exit(1)

        print(f"✅ {result.stdout.strip()}")

        # Open file if requested
        if args.view:
            try:
                if args.browser:
                    # Open in browser
                    import webbrowser
                    webbrowser.open(f'file://{output_file.absolute()}')
                    print(f"🌐 Opened in browser")
                else:
                    # Try to open with system default editor
                    if sys.platform.startswith('darwin'):  # macOS
                        subprocess.run(['open', str(output_file)])
                    elif sys.platform.startswith('linux'):  # Linux
                        subprocess.run(['xdg-open', str(output_file)])
                    elif sys.platform.startswith('win'):  # Windows
                        subprocess.run(['start', str(output_file)], shell=True)

                    print(f"📖 Opened {output_file.name}")

            except Exception as e:
                print(f"⚠️  Could not open file automatically: {e}")
                print(f"📁 File saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()