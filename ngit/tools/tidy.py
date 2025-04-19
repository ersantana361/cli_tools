from pathlib import Path
from git import Repo
import questionary
from rich.progress import Progress

def run_tidy(interactive: bool, granularity: str, console):
    repo = Repo(Path.cwd())
    
    with Progress(transient=True, console=console) as progress:
        task = progress.add_task("Analyzing changes...", total=None)
        diffs = repo.index.diff(None, create_patch=True)
        
        if interactive:
            changes = interactive_split(diffs, console)
        else:
            changes = auto_split(diffs, granularity)
            
        create_commits(repo, changes)
        progress.update(task, visible=False)
        console.print("[bold green]✓ Commits created successfully!")

def interactive_split(diffs, console):
    changes = {"structural": [], "behavioral": []}
    
    for diff in diffs:
        hunk = diff.diff.decode() if isinstance(diff.diff, bytes) else diff.diff
        console.print(f"\n[dim]{'-'*40}[/]")
        console.print(f"[bold cyan]{diff.a_path}[/]")
        
        choice = questionary.select(
            "Change type:",
            choices=[
                {"name": "🧹 Structural (refactor)", "value": "structural"},
                {"name": "🚀 Behavioral (feature/fix)", "value": "behavioral"},
                {"name": "⏭ Skip this change", "value": "skip"}
            ],
            qmark="▷"
        ).ask()
        
        if choice != "skip":
            changes[choice].append(hunk)
    
    return changes

def auto_split(diffs, granularity):
    # Simple classification logic
    return {
        "structural": [d.diff for d in diffs if b"rename" in d.diff],
        "behavioral": [d.diff for d in diffs if b"rename" not in d.diff]
    }

def create_commits(repo, changes):
    for change_type, patches in changes.items():
        if patches:
            repo.git.execute(["git", "reset", "--hard"])
            for patch in patches:
                repo.git.apply(patch)
            repo.git.add(update=True)
            repo.index.commit(f"{change_type.capitalize()} changes")
