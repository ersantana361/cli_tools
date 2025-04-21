import time
from pathlib import Path
from git import Repo
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def get_repo(path: Path) -> Repo:
    return Repo(path, search_parent_directories=True)

def create_backup(repo: Repo) -> str:
    """Create safety backup using Git's stash mechanism"""
    backup_id = str(int(time.time()))
    stash_sha = repo.git.stash("create", "-u")
    
    if not stash_sha:
        raise ValueError("No changes to create backup from")
    
    repo.git.update_ref(f"refs/ngit-backups/{backup_id}", stash_sha)
    return backup_id

def show_status(args, console: Console):
    try:
        repo = get_repo(Path(args.path))
        status = [
            f"🔍 Repository: {repo.working_dir}",
            f"🔀 Branch: {repo.active_branch.name}",
            f"📦 Last Commit: {repo.head.commit.hexsha[:7]}",
            f"📝 Unstaged Changes: {len(repo.index.diff(None))} file(s)"
        ]
        
        backups = [ref for ref in repo.references if "ngit-backups" in ref.name]
        status.append(f"\n🛡️ ngit Backups: {len(backups)} available")
        
        if backups:
            latest = max(backups, key=lambda r: r.commit.committed_date)
            status.append(f"   Latest: {latest.name.split('/')[-1]}")
            status.append(f"   Created: {latest.commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        console.print(Panel.fit("\n".join(status), title="Tidy First Status"))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")

def undo_operations(args, console: Console):
    try:
        repo = get_repo(Path(args.path))
        backups = sorted(
            [ref for ref in repo.references if "ngit-backups" in ref.name],
            key=lambda r: r.commit.committed_date,
            reverse=True
        )
        
        if not backups:
            console.print("[yellow]No backups found[/]")
            return

        target = backups[args.n-1]
        repo.git.reset("--hard", target.commit.hexsha)
        
        console.print(Panel.fit(
            f"[bold]⏮️ Restored to backup {target.name.split('/')[-1]}[/]",
            subtitle=f"Date: {target.commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")

def show_history(args, console: Console):
    try:
        repo = get_repo(Path(args.path))
        table = Table(show_header=False)
        
        for commit in repo.iter_commits(max_count=args.n):
            is_ngit = "ngit-id:" in commit.message
            msg = commit.message.split("\n")[0]
            table.add_row(
                f"[dim]{commit.hexsha[:7]}[/]",
                "[yellow]🧹[/]" if is_ngit else "[blue]🚀[/]",
                msg,
                f"[italic]{commit.author.name}[/]",
                f"[dim]{commit.committed_datetime.strftime('%Y-%m-%d')}[/]"
            )
            
        console.print(Panel.fit(table, title="Tidy First History"))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")
