import argparse
from pathlib import Path
from rich.console import Console
from tools.tidy import run_tidy

def main():
    parser = argparse.ArgumentParser(
        prog="ngit",
        description="Next-generation Git workflow tools",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Tidy Subcommand
    tidy_parser = subparsers.add_parser(
        "tidy",
        help="Organize working changes into semantic commits",
        description="""▓▒░ Structured Commit Creation ░▒▓

Operates exclusively on UNSTAGED changes in the working directory:
1. Analyzes modified files
2. Classifies changes using AST analysis
3. Creates new commits preserving original order
4. Leaves working directory clean

Safety Mechanisms:
├── Backup reference created at refs/gittidy-backup
├── Atomic operations - aborts on conflict
└── No existing commits are modified""",
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
        help="""Interactive mode:
- Review each change
- Override classifications
- Confirm before committing"""
    )
    tidy_parser.add_argument(
        "-g", "--granularity",
        choices=["atomic", "category"],
        default="category",
        help="""Commit grouping strategy:
atomic   - Individual changes
category - Group by type (default)"""
    )
    tidy_parser.add_argument(
        "-l", "--language",
        choices=["python", "js"],
        default="python",
        help="""Analysis language:
python - Full syntax tree analysis
js     - Basic pattern matching"""
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
                console=console
            )
        except KeyboardInterrupt:
            console.print("\n[bold red]Operation cancelled[/]")
            console.print("Recover with: [cyan]git reset --hard refs/gittidy-backup[/]")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            console.print("[yellow]Check backup: [cyan]git show refs/gittidy-backup[/]")

if __name__ == "__main__":
    main()
