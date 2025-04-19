import argparse
from rich.console import Console
from tools.github_agent import run_github
from tools.youtube_agent import run_youtube
from tools.pdf_converter import run_conversion

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Unified tool suite for document processing, GitHub PR analysis, and YouTube transcript analysis.\n\n"
            "Subcommands:\n"
            "  convert   Convert PDF documents to Markdown with rich formatting options\n"
            "  github    Analyze GitHub pull requests and generate reports\n"
            "  youtube   Analyze YouTube video transcripts and generate insights\n\n"
            "For detailed help: %(prog)s <command> -h"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Choose a subcommand to run")

    # Convert subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert PDF documents to Markdown",
        description=(
            "Advanced PDF conversion tool with rich feedback and processing options\n\n"
            "Features:\n"
            "  - Local files and URL support\n"
            "  - Progress tracking\n"
            "  - Multiple output formats\n"
            "  - Clipboard integration\n"
            "  - Verbose diagnostics"
        )
    )
    convert_parser.add_argument("input_source", 
                              help="PDF file path or URL")
    convert_parser.add_argument("-o", "--output", 
                              default="output.md",
                              help="Output file path (default: output.md)")
    convert_parser.add_argument("--verbose", action="store_true",
                              help="Show detailed processing information")
    convert_parser.add_argument("--format", choices=["basic", "enhanced"], 
                              default="basic",
                              help="Markdown formatting style (default: basic)")
    convert_parser.add_argument("--clipboard", action="store_true",
                              help="Copy result to clipboard")

    # GitHub subcommand (existing)
    github_parser = subparsers.add_parser(
        "github",
        help="Generate a PR report for a GitHub pull request.",
        description=(
            "Generate a GitHub pull request report by analyzing the diff of the PR.\n"
            "This command will:\n"
            "  - Fetch the diff from GitHub using the provided PR link.\n"
            "  - Invoke an LLM to analyze the diff and summarize key findings.\n"
            "  - Generate a formatted report (in either GitHub or Slack style).\n"
            "  - Show the current PR description and prompt to update it."
        )
    )
    github_parser.add_argument("pr_link", help="GitHub PR link (private repository)")
    github_parser.add_argument("--target", choices=["github", "slack"], default="github", 
                             help="Output format target (default: github)")

    # YouTube subcommand (existing)
    youtube_parser = subparsers.add_parser(
        "youtube",
        help="Generate a transcript analysis for a YouTube video.",
        description=(
            "Analyze a YouTube video by fetching its transcript and running a detailed analysis via an LLM.\n"
            "This command will:\n"
            "  - Extract the video ID and fetch the video title.\n"
            "  - Retrieve and format the transcript.\n"
            "  - Generate an analysis prompt and invoke the LLM to create an analysis report.\n"
            "  - Optionally generate dynamic tags and output a Markdown report."
        )
    )
    youtube_parser.add_argument("video", help="YouTube video ID or URL")
    youtube_parser.add_argument("--language", default="en", 
                              help="Language code (default: en)")
    youtube_parser.add_argument("--target", choices=["markdown", "slack"], default="markdown",
                              help="Output format option (default: markdown)")
    youtube_parser.add_argument("--prompt-only", action="store_true",
                              help="Generate the prompt only without invoking the LLM")
    youtube_parser.add_argument("--dynamic-tags", action="store_true",
                              help="Generate dynamic tags based on the analysis output")
    
    args = parser.parse_args()
    console = Console()

    if args.command == "convert":
        run_conversion(
            input_source=args.input_source,
            output_path=args.output,
            verbose=args.verbose,
            markdown_format=args.format,
            clipboard=args.clipboard,
            console=console
        )
    elif args.command == "github":
        run_github(pr_link=args.pr_link, target=args.target)
    elif args.command == "youtube":
        run_youtube(
            video=args.video,
            language=args.language,
            target=args.target,
            prompt_only=args.prompt_only,
            dynamic_tags=args.dynamic_tags
        )

if __name__ == "__main__":
    main()
