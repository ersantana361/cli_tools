#!/usr/bin/env python3
"""
API client for AI Tools - provides CLI interface to API endpoints
"""
import argparse
import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def make_request(endpoint: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Make API request and handle response"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        sys.exit(1)

def convert_pdf(args):
    """Convert PDF via API"""
    data = {
        "input_source": args.input_source,
        "format": args.format,
        "verbose": args.verbose
    }
    
    result = make_request("/api/v1/convert/pdf", data)
    
    if result["success"]:
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result["content"])
            print(f"PDF converted and saved to {args.output}")
        else:
            print(result["content"])
    else:
        print(f"Conversion failed: {result['error']}")
        sys.exit(1)

def analyze_github(args):
    """Analyze GitHub PR via API"""
    data = {
        "pr_link": args.pr_link,
        "target": args.target,
        "llm_provider": args.llm_provider
    }
    
    result = make_request("/api/v1/github/analyze-pr", data)
    
    if result["success"]:
        print(result["analysis"])
    else:
        print(f"Analysis failed: {result['error']}")
        sys.exit(1)

def analyze_youtube(args):
    """Analyze YouTube video via API"""
    data = {
        "video": args.video,
        "language": args.language,
        "target": args.target,
        "slack_thread": args.slack_thread,
        "slack_channel": args.slack_channel,
        "prompt_only": args.prompt_only,
        "dynamic_tags": args.dynamic_tags,
        "llm_provider": args.llm_provider
    }
    
    result = make_request("/api/v1/youtube/analyze", data)
    
    if result["success"]:
        print(result["analysis"])
    else:
        print(f"Analysis failed: {result['error']}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Tools API Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert PDF to Markdown")
    convert_parser.add_argument("input_source", help="PDF file path/URL")
    convert_parser.add_argument("-o", "--output", help="Output file path")
    convert_parser.add_argument("--verbose", action="store_true")
    convert_parser.add_argument("--format", choices=["basic", "enhanced"], default="basic")

    # GitHub command
    github_parser = subparsers.add_parser("github", help="Analyze GitHub PRs")
    github_parser.add_argument("pr_link", help="GitHub PR URL")
    github_parser.add_argument("--target", choices=["github", "slack"], default="github")
    github_parser.add_argument("--llm-provider", choices=["anthropic", "deepseek"], default="anthropic")

    # YouTube command
    youtube_parser = subparsers.add_parser("youtube", help="Analyze YouTube videos")
    youtube_parser.add_argument("video", nargs="?", help="YouTube URL")
    youtube_parser.add_argument("--language", default="en")
    youtube_parser.add_argument("--target", choices=["markdown", "slack"], default="markdown")
    youtube_parser.add_argument("--slack-thread", help="Slack thread URL")
    youtube_parser.add_argument("--slack-channel", help="Slack channel name")
    youtube_parser.add_argument("--prompt-only", action="store_true")
    youtube_parser.add_argument("--dynamic-tags", action="store_true")
    youtube_parser.add_argument("--llm-provider", choices=["anthropic", "deepseek"], default="anthropic")

    args = parser.parse_args()

    if args.command == "convert":
        convert_pdf(args)
    elif args.command == "github":
        analyze_github(args)
    elif args.command == "youtube":
        analyze_youtube(args)

if __name__ == "__main__":
    main()