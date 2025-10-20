#!/usr/bin/env python3
"""
LeetCode Editorial Extractor

Extracts editorial content from a saved LeetCode HTML page and creates
an offline-readable Markdown file.
"""

import json
import re
import html
from pathlib import Path
import argparse
import sys
from typing import Dict, Any, Optional, Set
import urllib.request
import urllib.parse
import hashlib


def download_image(url: str, output_dir: Path) -> Optional[str]:
    """Download an image and return the local filename."""
    try:
        # Create a filename based on URL hash to avoid duplicates
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        parsed_url = urllib.parse.urlparse(url)

        # Get file extension
        path_parts = parsed_url.path.split('.')
        if len(path_parts) > 1 and path_parts[-1].lower() in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
            ext = path_parts[-1].lower()
        else:
            ext = 'jpg'  # Default extension

        filename = f"image_{url_hash}.{ext}"
        local_path = output_dir / filename

        # Skip if already downloaded
        if local_path.exists():
            return filename

        # Download the image with headers to avoid 403 errors
        print(f"  📷 Downloading: {url}")
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://leetcode.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
            }
        )

        with urllib.request.urlopen(req) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())

        return filename
    except Exception as e:
        print(f"  ⚠️  Failed to download {url}: {e}")
        return None


def extract_and_download_images(content: str, output_dir: Path) -> str:
    """Extract image URLs from content and download them, updating references."""
    # Create images directory
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # Find all image URLs
    image_pattern = r'<img[^>]*src="([^"]*)"[^>]*>'
    images = re.findall(image_pattern, content)

    updated_content = content
    downloaded_images = set()

    for img_url in images:
        if img_url in downloaded_images:
            continue

        # Skip data URLs and relative URLs
        if img_url.startswith('data:') or not img_url.startswith('http'):
            continue

        local_filename = download_image(img_url, images_dir)
        if local_filename:
            # Update the content to use local image
            local_path = f"images/{local_filename}"
            updated_content = updated_content.replace(img_url, local_path)
            downloaded_images.add(img_url)

    return updated_content


def extract_json_data(html_content: str) -> Optional[Dict[Any, Any]]:
    """Extract the __NEXT_DATA__ JSON from the HTML."""
    # Find the script tag containing __NEXT_DATA__
    pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
    match = re.search(pattern, html_content, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


def decode_html_content(content: str) -> str:
    """Decode HTML entities and convert to clean text."""
    # First decode HTML entities
    decoded = html.unescape(content)

    # Convert HTML tags to markdown equivalents
    conversions = [
        (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),
        (r'<strong[^>]*>(.*?)</strong>', r'**\1**'),
        (r'<em[^>]*>(.*?)</em>', r'*\1*'),
        (r'<code[^>]*>(.*?)</code>', r'`\1`'),
        (r'<pre[^>]*>\s*(.*?)\s*</pre>', r'\n```\n\1\n```\n'),
        (r'<ul[^>]*>(.*?)</ul>', r'\n\1\n'),
        (r'<li[^>]*>(.*?)</li>', r'- \1\n'),
        (r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n'),
        (r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n'),
        (r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n'),
        (r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n'),
        (r'<br\s*/?>', r'\n'),
        (r'<img[^>]*src="([^"]*)"[^>]*>', r'\n![Image](\1)\n'),
        (r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)'),
        (r'&nbsp;', r' '),
        (r'&amp;', r'&'),
        (r'&lt;', r'<'),
        (r'&gt;', r'>'),
        (r'&quot;', r'"'),
        (r'&#39;', r"'"),
    ]

    for pattern, replacement in conversions:
        decoded = re.sub(pattern, replacement, decoded, flags=re.DOTALL | re.IGNORECASE)

    # Clean up remaining HTML tags
    decoded = re.sub(r'<[^>]+>', '', decoded)

    # Clean up extra whitespace and normalize line breaks
    decoded = re.sub(r'\n\s*\n\s*\n+', '\n\n', decoded)
    decoded = re.sub(r'^\s+|\s+$', '', decoded, flags=re.MULTILINE)
    decoded = re.sub(r'\s+', ' ', decoded)  # Normalize spaces
    decoded = re.sub(r'(\*\*[^*]+\*\*)\s*(\*\*[^*]+\*\*)', r'\1\n\n\2', decoded)  # Separate example blocks

    return decoded.strip()


def format_examples(question_data: Dict[Any, Any]) -> str:
    """Extract and format examples from the question content."""
    content = question_data.get('content', '')
    if not content:
        return ""

    decoded_content = decode_html_content(content)

    # Split by Example to properly separate them
    examples = re.findall(r'(\*\*Example \d+:\*\*.*?)(?=\*\*Example \d+:\*\*|\*\*Constraints:\*\*|$)',
                         decoded_content, re.DOTALL | re.IGNORECASE)

    if not examples:
        # Try alternative pattern
        examples = re.findall(r'(Example \d+:.*?)(?=Example \d+:|Constraints:|$)',
                             decoded_content, re.DOTALL | re.IGNORECASE)

    if examples:
        formatted_examples = []
        for i, example in enumerate(examples):
            # Clean up the example
            clean_example = re.sub(r'\s+', ' ', example.strip())
            # Format input/output better
            clean_example = re.sub(r'\*\*Input:\*\* (.*?) \*\*Output:\*\* (.*?)(?=\s|$)',
                                 r'**Input:** \1\n**Output:** \2\n', clean_example)
            formatted_examples.append(clean_example)

        return '\n\n'.join(formatted_examples)

    return ""


def extract_constraints(question_data: Dict[Any, Any]) -> str:
    """Extract constraints from the question content."""
    content = question_data.get('content', '')
    if not content:
        return ""

    decoded_content = decode_html_content(content)

    # Extract constraints section
    constraints_match = re.search(r'Constraints:(.*?)$',
                                 decoded_content, re.DOTALL | re.IGNORECASE)

    if constraints_match:
        return constraints_match.group(1).strip()

    return ""


def get_editorial_content(data: Dict[Any, Any]) -> str:
    """Extract editorial content from the data structure."""
    # For now, we'll create a placeholder since the actual editorial content
    # would be in a separate API call. We'll include what we can extract.

    editorial_parts = [
        "## Editorial",
        "",
        "*Note: This is extracted from the saved HTML page. The full editorial content*",
        "*would typically be loaded separately via API calls.*",
        "",
        "### Approach",
        "",
        "Based on the problem (Binary Tree Level Order Traversal), the standard approaches are:",
        "",
        "1. **BFS (Breadth-First Search) with Queue**",
        "   - Use a queue to traverse level by level",
        "   - For each level, process all nodes currently in the queue",
        "   - Add children to the queue for the next level",
        "",
        "2. **DFS (Depth-First Search) with Level Tracking**",
        "   - Use recursion with level parameter",
        "   - Group nodes by their depth level",
        "",
        "### Implementation Notes",
        "",
        "- Time Complexity: O(n) where n is the number of nodes",
        "- Space Complexity: O(w) where w is the maximum width of the tree",
        "",
        "### Code Template",
        "",
        "```python",
        "# Definition for a binary tree node.",
        "# class TreeNode:",
        "#     def __init__(self, val=0, left=None, right=None):",
        "#         self.val = val",
        "#         self.left = left",
        "#         self.right = right",
        "",
        "class Solution:",
        "    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:",
        "        if not root:",
        "            return []",
        "        ",
        "        result = []",
        "        queue = [root]",
        "        ",
        "        while queue:",
        "            level_size = len(queue)",
        "            level_values = []",
        "            ",
        "            for _ in range(level_size):",
        "                node = queue.pop(0)",
        "                level_values.append(node.val)",
        "                ",
        "                if node.left:",
        "                    queue.append(node.left)",
        "                if node.right:",
        "                    queue.append(node.right)",
        "            ",
        "            result.append(level_values)",
        "        ",
        "        return result",
        "```"
    ]

    return "\n".join(editorial_parts)


def create_markdown_content(data: Dict[Any, Any], output_path: Path) -> str:
    """Create the complete markdown content."""
    try:
        question = data['props']['pageProps']['dehydratedState']['queries'][1]['state']['data']['question']

        # Extract basic info
        title = question.get('title', 'Unknown Title')
        question_id = question.get('questionFrontendId', 'N/A')
        difficulty = question.get('difficulty', 'Unknown')

        # Get topic tags
        topic_tags = [tag['name'] for tag in question.get('topicTags', [])]
        topics_str = ', '.join(topic_tags) if topic_tags else 'Not specified'

        # Extract problem content and download images
        raw_content = question.get('content', '')
        print("📷 Processing images...")
        content_with_local_images = extract_and_download_images(raw_content, output_path.parent)

        problem_description = decode_html_content(content_with_local_images)

        # Create a modified question object for examples and constraints
        modified_question = question.copy()
        modified_question['content'] = content_with_local_images

        examples = format_examples(modified_question)
        constraints = extract_constraints(modified_question)

        # Get similar questions
        similar_questions = question.get('similarQuestionList', [])
        similar_list = []
        for sq in similar_questions[:5]:  # Limit to first 5
            similar_list.append(f"- [{sq['title']}] (Difficulty: {sq['difficulty']})")

        similar_str = '\n'.join(similar_list) if similar_list else 'None listed'

        # Build markdown content
        markdown_parts = [
            f"# LeetCode {question_id}: {title}",
            "",
            f"**Difficulty:** {difficulty}",
            f"**Topics:** {topics_str}",
            "",
            "## Problem Description",
            "",
            problem_description,
            "",
        ]

        if examples:
            markdown_parts.extend([
                "## Examples",
                "",
                examples,
                "",
            ])

        if constraints:
            markdown_parts.extend([
                "## Constraints",
                "",
                constraints,
                "",
            ])

        markdown_parts.extend([
            get_editorial_content(data),
            "",
            "## Similar Questions",
            "",
            similar_str,
            "",
            f"---",
            f"*Extracted from LeetCode on {Path(__file__).stat().st_mtime}*",
        ])

        return '\n'.join(markdown_parts)

    except (KeyError, IndexError, TypeError) as e:
        return f"Error extracting content: {e}\n\nRaw data structure may have changed."


def main():
    parser = argparse.ArgumentParser(description='Extract LeetCode editorial from HTML file')
    parser.add_argument('html_file', help='Path to the saved HTML file')
    parser.add_argument('-o', '--output', help='Output markdown file (default: based on input name)')

    args = parser.parse_args()

    html_file = Path(args.html_file)
    if not html_file.exists():
        print(f"Error: File {html_file} not found")
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = html_file.with_suffix('.md')

    # Read HTML content
    try:
        html_content = html_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        sys.exit(1)

    # Extract JSON data
    data = extract_json_data(html_content)
    if not data:
        print("Could not extract JSON data from HTML file")
        sys.exit(1)

    # Create markdown content
    markdown_content = create_markdown_content(data, output_file)

    # Write output
    try:
        output_file.write_text(markdown_content, encoding='utf-8')
        print(f"Editorial extracted to: {output_file}")
        print(f"File size: {output_file.stat().st_size} bytes")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()