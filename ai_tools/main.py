import argparse
from rich.console import Console
from tools.github_agent import run_github
from tools.youtube_agent import run_youtube, run_youtube_batch
from tools.pdf_converter import run_conversion

def validate_slack_args(args):
    """Ensure Slack thread or channel is provided when target is slack"""
    if args.command == "youtube" and args.target == "slack":
        if not args.slack_thread and not args.slack_channel:
            raise ValueError("Either --slack-thread URL or --slack-channel name required for 'slack' target")
        if args.slack_thread and args.slack_channel:
            raise ValueError("Use either --slack-thread or --slack-channel, not both")
        # When using slack target, video URL can be auto-extracted from thread/channel
        # No need to validate video URL here - let youtube_agent handle it

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered YouTube Video Analyzer with Slack Integration",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert PDF to Markdown"
    )
    convert_parser.add_argument("input_source", help="PDF file path/URL")
    convert_parser.add_argument("-o", "--output", default="output.md")
    convert_parser.add_argument("--verbose", action="store_true")
    convert_parser.add_argument("--format", choices=["basic", "enhanced"], default="basic")
    convert_parser.add_argument("--clipboard", action="store_true")

    # GitHub command
    github_parser = subparsers.add_parser(
        "github",
        help="Analyze GitHub PRs"
    )
    github_parser.add_argument("pr_link", help="GitHub PR URL")
    github_parser.add_argument("--target", choices=["github", "slack"], default="github")
    github_parser.add_argument(
        "--llm-provider",
        choices=["anthropic", "deepseek"],
        default="anthropic", # Default to Anthropic
        help="Specify the LLM provider to use (anthropic or deepseek)"
    )

    # YouTube command (updated)
    youtube_parser = subparsers.add_parser(
        "youtube",
        help="Analyze YouTube videos",
        description="""YouTube Video Analysis Command
---------------------------------
Single video:
  youtube "https://youtu.be/VIDEO_ID" --target markdown --save-file

Multiple videos:
  youtube "URL1" "URL2" "URL3" --target markdown --save-file

Playlist:
  youtube "https://youtube.com/playlist?list=PLAYLIST_ID" --target markdown --save-file

When using Slack target:
  Required: --slack-thread "https://slack.com/archives/CHANNEL_ID/pTIMESTAMP"

Examples:
  Single:   youtube "https://youtu.be/VIDEO_ID" --target markdown --save-file
  Batch:    youtube "URL1" "URL2" --target markdown --save-file
  Playlist: youtube "https://youtube.com/playlist?list=..." --target markdown --save-file
  Slack:    youtube "https://youtu.be/VIDEO_ID" --target slack --slack-thread URL
  Auto-extract from thread: youtube --target slack --slack-thread URL
  Auto-extract from channel: youtube --target slack --slack-channel erick-chatbot-room"""
    )
    youtube_parser.add_argument(
        "video",
        nargs="*",  # Accept zero or more video URLs for batch processing
        help="YouTube URL(s). Can be: single video URL, multiple video URLs, or playlist URL(s). Optional when using --target slack (will be auto-extracted from thread)"
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
        required=True,
        help="Output target format"
    )
    youtube_parser.add_argument(
        "--slack-thread",
        help="Slack thread URL (required for 'slack' target)"
    )
    youtube_parser.add_argument(
        "--slack-channel",
        help="Slack channel name to get latest message from (alternative to --slack-thread)"
    )
    youtube_parser.add_argument(
        "--ask-for-url",
        action="store_true",
        help="Prompt for YouTube URL input (workaround for Slack permission issues)"
    )
    youtube_parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Generate prompt without LLM analysis"
    )
    youtube_parser.add_argument(
        "--dynamic-tags",
        action="store_true",
        help="Generate dynamic content tags (markdown only)"
    )
    # NEW: Argument to select LLM provider for YouTube command
    youtube_parser.add_argument(
        "--llm-provider",
        choices=["anthropic", "deepseek"],
        default="anthropic", # Default to Anthropic
        help="Specify the LLM provider to use (anthropic or deepseek)"
    )
    youtube_parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save output to markdown file(s) (default: clipboard only for single video, auto-save for batch)"
    )
    youtube_parser.add_argument(
        "-o", "--output",
        help="Custom output filename (only for single video, ignored in batch mode)"
    )


    args = parser.parse_args()
    console = Console()

    try:
        # Validate Slack requirements
        validate_slack_args(args)

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
                target=args.target,
                llm_provider=args.llm_provider
            )
        elif args.command == "youtube":
            # Determine if batch or single video processing
            # Handle case where video is a list (could be empty, single, or multiple)
            video_input = args.video if isinstance(args.video, list) else [args.video] if args.video else []

            # Check if we need batch processing (multiple videos or playlist)
            needs_batch = len(video_input) > 1 or (len(video_input) == 1 and "list=" in video_input[0])

            # Validate: batch processing requires --save-file flag
            if needs_batch and args.target == "markdown" and not args.save_file:
                console.print("\n[bold red]⚠️  Batch Processing Requires File Output[/bold red]\n")
                console.print("You're trying to process multiple videos or a playlist.")
                console.print("Multiple analyses cannot be output to clipboard only.\n")
                console.print("[bold cyan]Please add the --save-file flag:[/bold cyan]")

                if len(video_input) > 1:
                    console.print(f"  python ai_tools/main.py youtube URL1 URL2 ... --target markdown [bold green]--save-file[/bold green]")
                else:
                    console.print(f"  python ai_tools/main.py youtube \"PLAYLIST_URL\" --target markdown [bold green]--save-file[/bold green]")

                console.print("\n[dim]This will save each video to a separate .md file in the current directory.[/dim]\n")
                exit(1)

            if needs_batch and args.target == "markdown":
                # Batch processing for multiple videos or playlists
                run_youtube_batch(
                    video_urls=video_input,
                    language=args.language,
                    target=args.target,
                    prompt_only=args.prompt_only,
                    dynamic_tags=args.dynamic_tags,
                    llm_provider=args.llm_provider,
                    save_file=True  # Always save files in batch mode
                )
            else:
                # Single video processing (or Slack mode)
                single_video = video_input[0] if video_input else None
                run_youtube(
                    video=single_video,
                    language=args.language,
                    target=args.target,
                    prompt_only=args.prompt_only,
                    dynamic_tags=args.dynamic_tags,
                    slack_thread_url=args.slack_thread,
                    slack_channel_name=args.slack_channel,
                    ask_for_url=args.ask_for_url,
                    llm_provider=args.llm_provider,
                    save_file=args.save_file,
                    output_file=args.output
                )

    except ValueError as e:
        console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
        if args.command == "youtube" and "slack" in str(e).lower():
            youtube_parser.print_help()
        exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
