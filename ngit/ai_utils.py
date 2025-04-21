import os
import requests
from typing import Optional
from rich.console import Console

console = Console()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def needs_ai_key():
    """Check if API key is available"""
    if not os.getenv("DEEPSEEK_API_KEY"):
        console.print("[red]Error:[/] Deepseek API key required for AI features")
        console.print("Get a key at [blue]https://platform.deepseek.com[/]")
        console.print("Then run: [white]export DEEPSEEK_API_KEY='your-key'[/]")
        raise ValueError("Missing DEEPSEEK_API_KEY")

def generate_commit_message(diff: str, change_type: str) -> Optional[str]:
    """Generate commit message using Deepseek's API"""
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-coder-33b-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": f"""You're a senior engineer practicing Tidy First. 
                        Generate a conventional commit message for {change_type} changes.
                        Use 'chore' for structural, 'feat'/'fix' for behavioral.
                        Keep under 72 characters."""
                    },
                    {
                        "role": "user",
                        "content": f"Changes:\n{diff}"
                    }
                ],
                "temperature": 0.2
            }
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
            
        console.print(f"[yellow]API Error ({response.status_code}):[/] {response.text}")
        return f"{change_type.capitalize()} changes (AI failed)"
        
    except Exception as e:
        console.print(f"[red]AI Error:[/] {str(e)}")
        return f"{change_type.capitalize()} changes"
