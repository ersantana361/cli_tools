import argparse
from rich.console import Console
from core import tidy_workflow
from git_utils import show_status, undo_operations, show_history
from ai_utils import needs_ai_key

print('test')

console = Console()

def main():
    parser = argparse.ArgumentParser(
        prog="ngit",
        description="Tidy First Git Workflows by Kent Beck",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Tidy command
    tidy_parser = subparsers.add_parser("tidy", help="Organize changes using Tidy First")
    tidy_parser.add_argument("path", nargs="?", default=".")
    tidy_parser.add_argument("--ai", action="store_true")
    tidy_parser.add_argument("-l", "--language", choices=["python", "js"], default="python")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show repository status")
    status_parser.add_argument("path", nargs="?", default=".")
    
    # Undo command
    undo_parser = subparsers.add_parser("undo", help="Revert changes")
    undo_parser.add_argument("path", nargs="?", default=".")
    undo_parser.add_argument("-n", type=int, default=1)
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show commit history")
    history_parser.add_argument("path", nargs="?", default=".")
    history_parser.add_argument("-n", type=int, default=10)

    args = parser.parse_args()
    
    try:
        if args.command == "tidy":
            if args.ai: needs_ai_key()
            tidy_workflow(args, console)
        elif args.command == "status":
            show_status(args, console)
        elif args.command == "undo":
            undo_operations(args, console)
        elif args.command == "history":
            show_history(args, console)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")

if __name__ == "__main__":
    main()
