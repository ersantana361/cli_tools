import argparse
from pathlib import Path
from rich.console import Console
from tools.tidy import run_tidy

def main():
    parser = argparse.ArgumentParser(
        prog="ngit",
        description="Next-generation Git workflow tools with AI integration",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Tidy Subcommand
    tidy_parser = subparsers.add_parser(
        "tidy",
        help="Organize changes into semantic commits with AI support",
        description="""▓▒░ Structured Commit Creation ░▒▓

Features:
├── AST-based change classification
├── AI-powered commit messages (--ai)
├── Interactive review mode (-i)
├── Automatic Git state backups
└── Multi-language support

AI Requirements:
- DEEPSEEK_API_KEY environment variable
- Internet connection""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    tidy_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to Git repository (default: current directory)"
    )
    tidy_parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Step through changes with visual confirmation"
    )
    tidy_parser.add_argument(
        "-g", "--granularity",
        choices=["atomic", "category"],
        default="category",
        help="Commit grouping strategy"
    )
    tidy_parser.add_argument(
        "-l", "--language",
        choices=["python", "js"],
        default="python",
        help="Analysis language"
    )
    tidy_parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate semantic commit messages using LLM"
    )

    args = parser.parse_args()
    console = Console()

    if args.command == "tidy":
        try:
            run_tidy(
                repo_path=Path(args.path).resolve(),
                interactive=args.interactive,
                granularity=args.granularity,
                language=args.language,
                console=console,
                use_ai=args.ai
            )
        except KeyboardInterrupt:
            console.print("\n[bold red]Operation cancelled[/]")
            console.print("Recover with: [cyan]git reset --hard refs/gittidy-backup[/]")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")

if __name__ == "__main__":
    main()
