import ast
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from git_utils import get_repo, create_backup
from ai_utils import generate_commit_message

class ChangeClassifier:
    def __init__(self, language: str = "python"):
        self.language = language
        
    def classify(self, old_code: str, new_code: str) -> str:
        """Classify changes as structural or behavioral"""
        if self.language == "python":
            return self._classify_python(old_code, new_code)
        return "behavioral"

    def _classify_python(self, old: str, new: str) -> str:
        """Python-specific classification using AST analysis"""
        try:
            old_ast = ast.parse(old)
            new_ast = ast.parse(new)
            if self._is_pure_rename(old_ast, new_ast) or self._only_formatting(old, new):
                return "structural"
        except SyntaxError:
            pass
        return "behavioral"

    def _is_pure_rename(self, old_ast, new_ast) -> bool:
        """Detect pure identifier renaming"""
        return ast.dump(old_ast) == ast.dump(new_ast)

    def _only_formatting(self, old: str, new: str) -> bool:
        """Detect whitespace-only changes"""
        return old.strip() == new.strip()

def tidy_workflow(args, console: Console):
    """Tidy First core workflow implementation"""
    try:
        repo = get_repo(Path(args.path))
        console.print(Panel.fit(
            "[bold]🧹 Tidy First Workflow[/]",
            subtitle=f"Repository: {repo.working_dir}",
            style="blue"
        ))

        # Stage all changes
        repo.git.add(A=True)
        repo.git.add(u=True)
        backup_ref = create_backup(repo)

        classifier = ChangeClassifier(args.language)
        changes = {"structural": [], "behavioral": []}

        # Classify changes
        for diff in repo.head.commit.diff(None, create_patch=True):
            if diff.change_type in ('M', 'A', 'D'):
                change_type = "behavioral"
                
                if diff.change_type == 'D':
                    change_type = "structural"
                elif diff.change_type == 'M':
                    old = "\n".join([line[1:] for line in diff.diff.splitlines() if line.startswith("-")])
                    new = "\n".join([line[1:] for line in diff.diff.splitlines() if line.startswith("+")])
                    change_type = classifier.classify(old, new)
                
                changes[change_type].append(diff.diff)

        # Create commits
        for change_type, diffs in changes.items():
            if diffs:
                patch_file = f"{change_type}.patch"
                with open(patch_file, "w") as f:
                    f.write("\n".join(diffs))
                
                repo.git.apply(patch_file)
                repo.git.add(update=True)
                
                if args.ai:
                    console.print(f"\n[dim]🤖 Analyzing {len(diffs)} {change_type} changes...[/]")
                    message = generate_commit_message("\n".join(diffs), change_type)
                    console.print(f"[dim]📝 Generated message: {message}[/]")
                else:
                    message = f"{change_type.capitalize()} changes ({len(diffs)} files)"
                
                repo.index.commit(message)
                os.remove(patch_file)

        console.print(f"\n🔒 Backup ID: [cyan]{backup_ref}[/]")
        console.print(f"   Restore: [white]git reset --hard {backup_ref}[/]")
        console.print("[green]✓ Successfully applied Tidy First![/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise
