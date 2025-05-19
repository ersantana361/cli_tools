#!/usr/bin/env python3
import time
import sys
import argparse
from pathlib import Path
from git import Repo, GitCommandError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def get_repo(path: Path) -> Repo:
    return Repo(path, search_parent_directories=True)


def create_backup(repo: Repo) -> str:
    """Create a safety backup using Git's stash mechanism and record it under ngit-backups"""
    backup_id = str(int(time.time()))
    # Stash with a message so we can identify it
    repo.git.stash("push", "-u", "-m", f"ngit-id:{backup_id}")
    # Grab the SHA of the latest stash entry
    stash_sha = repo.git.rev_parse("refs/stash")
    # Copy it into our own backups namespace
    repo.git.update_ref(f"refs/ngit-backups/{backup_id}", stash_sha)
    return backup_id


def show_status(repo: Repo, console: Console):
    status = [
        f"🔍 Repository: {repo.working_dir}",
        f"🔀 Branch: {repo.active_branch.name}",
        f"📦 Last Commit: {repo.head.commit.hexsha[:7]}",
        f"📝 Unstaged Changes: {len(repo.index.diff(None))} file(s)"
    ]
    # List our backups
    backups = [r for r in repo.refs if r.path.startswith('refs/ngit-backups/')]
    status.append(f"\n🛡️ ngit Backups: {len(backups)} available")
    if backups:
        latest = max(backups, key=lambda r: r.commit.committed_date)
        status.append(f"   Latest ID: {latest.name.split('/')[-1]}")
        status.append(f"   Created: {latest.commit.committed_datetime:%Y-%m-%d %H:%M:%S}")

    console.print(Panel.fit("\n".join(status), title="Tidy First Status"))


def undo_operations(repo: Repo, console: Console, n: int):
    backups = sorted(
        [r for r in repo.refs if r.path.startswith('refs/ngit-backups/')],
        key=lambda r: r.commit.committed_date,
        reverse=True
    )
    if not backups:
        console.print("[yellow]No backups found[/]")
        return

    if n < 1 or n > len(backups):
        console.print(f"[red]Invalid backup index: {n}[/]")
        return

    target = backups[n-1]
    repo.git.reset("--hard", target.commit.hexsha)
    console.print(
        Panel.fit(
            f"[bold]⏮️ Restored to backup {target.name.split('/')[-1]}[/]",
            subtitle=f"Date: {target.commit.committed_datetime:%Y-%m-%d %H:%M:%S}",
            style="green"
        )
    )


def show_history(repo: Repo, console: Console, n: int):
    table = Table(show_header=False)
    for commit in repo.iter_commits(max_count=n):
        short_sha = commit.hexsha[:7]
        msg = commit.message.split("\n")[0]
        is_backup = any(
            ref.commit.hexsha == commit.hexsha and ref.path.startswith('refs/ngit-backups/')
            for ref in repo.refs
        )
        icon = "[yellow]🧹[/]" if is_backup else "[blue]🚀[/]"
        table.add_row(
            f"[dim]{short_sha}[/]",
            icon,
            msg,
            f"[italic]{commit.author.name}[/]",
            f"[dim]{commit.committed_datetime:%Y-%m-%d}[/]"
        )
    console.print(Panel.fit(table, title="Tidy First History"))


def update_branch(repo: Repo, console: Console, remote: str, upstream: str):
    branch = repo.active_branch.name
    console.print(f"🔄 Fetching {upstream} from {remote}...")
    repo.git.fetch(remote, upstream)
    console.print(f"🔁 Rebasing {branch} onto {remote}/{upstream}...")
    repo.git.rebase(f"{remote}/{upstream}")
    console.print(f"🚀 Pushing {branch} to {remote} with --force-with-lease...")
    repo.git.push("--force-with-lease", remote, branch)
    console.print(f"✅ Branch {branch} is up-to-date!")


def main():
    parser = argparse.ArgumentParser(prog="ngit", description="A smarter git helper")
    parser.add_argument("--path", default='.', help="Path to your Git repo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show repository status")
    sub.add_parser("backup", help="Create a safety backup")
    undo = sub.add_parser("undo", help="Restore to a previous backup")
    undo.add_argument("n", type=int, help="Backup index (1 = latest)")
    hist = sub.add_parser("history", help="Show commit & backup history")
