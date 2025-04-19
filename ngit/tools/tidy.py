import ast
import os
import subprocess
from pathlib import Path
from typing import Dict, List
from git import Repo, Diff
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from langchain_openai import ChatOpenAI

class ChangeClassifier:
    def __init__(self, language: str = "python"):
        self.language = language
        
    def classify(self, old_code: str, new_code: str) -> str:
        if self.language == "python":
            return self._classify_python(old_code, new_code)
        return "behavioral"

    def _classify_python(self, old: str, new: str) -> str:
        try:
            old_ast = ast.parse(old)
            new_ast = ast.parse(new)
            if self._is_pure_rename(old_ast, new_ast) or self._only_formatting(old, new):
                return "structural"
        except SyntaxError:
            pass
        return "behavioral"

    def _is_pure_rename(self, old_ast, new_ast) -> bool:
        old_names = {n.id for n in ast.walk(old_ast) if isinstance(n, ast.Name)}
        new_names = {n.id for n in ast.walk(new_ast) if isinstance(n, ast.Name)}
        return old_names != new_names and ast.dump(old_ast) == ast.dump(new_ast)

    def _only_formatting(self, old: str, new: str) -> bool:
        return old.strip() == new.strip()

def generate_commit_message(diff: str, change_type: str) -> str:
    """Generate conventional commit message using LLM"""
    llm = ChatOpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        model_name="deepseek-chat"
    )
    
    prompt = f"""Generate a conventional commit message for these {change_type} changes:

Rules:
1. Use imperative mood ("Add" not "Added")
2. Start with type: {"chore/refactor" if change_type == "structural" else "feat/fix"}
3. Include scope if appropriate (e.g., "auth", "payment")
4. Max 50 characters subject line
5. Body explains WHY not WHAT
6. Format:
   
<type>(<scope>): <subject>

<body>

Diff:
{diff[:2000]}"""

    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"{change_type.capitalize()} changes (AI failed: {str(e)})"

def create_commits(repo, changes: Dict[str, List[str]], use_ai: bool):
    """Create commits with optional AI-generated messages"""
    for change_type, patches in changes.items():
        if patches:
            patch_file = f"{change_type}.patch"
            with open(patch_file, "w") as f:
                f.write("\n".join(patches))
            
            subprocess.run(["git", "apply", patch_file], check=True)
            repo.git.add(update=True)
            
            if use_ai:
                diff = "\n".join(patches)
                message = generate_commit_message(diff, change_type)
            else:
                message = f"{change_type.capitalize()} changes"
                
            repo.index.commit(message)
            os.remove(patch_file)

def run_tidy(repo_path: Path, interactive: bool, granularity: str, 
            language: str, console: Console, use_ai: bool = False):
    """Main tidy workflow with AI integration"""
    try:
        console.print(Panel.fit("[bold]🧹 ngit tidy - Commit Organization[/]", style="blue"))
        repo = Repo(repo_path)
        
        # Create backup
        backup_hash = repo.git.stash("create")
        console.print(f"🔒 Backup created at [cyan]{backup_hash[:7]}[/]")
        
        # Classify changes
        classifier = ChangeClassifier(language)
        diffs = repo.index.diff(None, create_patch=True)
        changes = {"structural": [], "behavioral": []}
        
        for diff in diffs:
            if diff.change_type == "M":
                for hunk in diff.diff.split('\n@@'):
                    old = "\n".join([line[1:] for line in hunk.splitlines() if line.startswith("-")])
                    new = "\n".join([line[1:] for line in hunk.splitlines() if line.startswith("+")])
                    change_type = classifier.classify(old, new)
                    changes[change_type].append(hunk)

        # Commit creation
        if use_ai:
            console.print("🧠 Using AI for commit messages (DEEPSEEK_API_KEY required)")
        create_commits(repo, changes, use_ai)
        
        console.print("[bold green]✓ Commits created successfully!")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if backup_hash:
            console.print(f"🔧 Restore with: [cyan]git reset --hard {backup_hash}[/]")
