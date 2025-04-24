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
            "  convert   Convert PDF documents to Markdown\n"
            "  github    Analyze GitHub pull requests\n"
            "  youtube   Analyze YouTube videos and post to Slack threads\n\n"
            "For detailed help: %(prog)s <command> -h"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert PDF documents to Markdown",
        description="Advanced PDF conversion with rich formatting options"
    )
    convert_parser.add_argument("input_source", help="PDF file path or URL")
    convert_parser.add_argument("-o", "--output", default="output.md")
    convert_parser.add_argument("--verbose", action="store_true")
    convert_parser.add_argument("--format", choices=["basic", "enhanced"], default="basic")
    convert_parser.add_argument("--clipboard", action="store_true")

    # GitHub subcommand
    github_parser = subparsers.add_parser(
        "github",
        help="Generate GitHub PR reports",
        description="Analyze pull requests and generate formatted reports"
    )
    github_parser.add_argument("pr_link", help="GitHub PR link")
    github_parser.add_argument("--target", choices=["github", "slack"], default="github")

    # YouTube subcommand (updated)
    youtube_parser = subparsers.add_parser(
        "youtube",
        help="Analyze YouTube videos",
        description=(
            "Analyze YouTube videos and post summaries to Slack threads\n\n"
            "When using --target slack, you must provide:\n"
            "  --slack-thread 'SLACK_THREAD_URL'"
        )
    )
    youtube_parser.add_argument(
        "video",
        help="YouTube URL (e.g. https://www.youtube.com/watch?v=VIDEO_ID)"
    )
    youtube_parser.add_argument(
        "--language",
        default="en",
        help="Transcript language code (default: en)"
    )
    youtube_parser.add_argument(
        "--target",
        choices=["markdown", "slack"],
        default="markdown",
        help="Output target (required for Slack)"
    )
    youtube_parser.add_argument(
        "--slack-thread",
        help="Slack thread URL to post to (required for Slack target)"
    )
    youtube_parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Generate prompt without LLM analysis"
    )
    youtube_parser.add_argument(
        "--dynamic-tags",
        action="store_true",
        help="Generate dynamic content tags"
    )

    args = parser.parse_args()
    console = Console()

    try:
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
            run_github(
                pr_link=args.pr_link,
                target=args.target
            )
        elif args.command == "youtube":
            run_youtube(
                video=args.video,
                language=args.language,
                target=args.target,
                prompt_only=args.prompt_only,
                dynamic_tags=args.dynamic_tags,
                slack_thread_url=args.slack_thread
            )
            
    except Exception as e:
        console.print(f"[bold red]💥 Critical Error: {str(e)}[/bold red]")
        if hasattr(e, "errno"):
            console.print(f"Error code: {e.errno}")
        exit(1)

if __name__ == "__main__":
    main()
