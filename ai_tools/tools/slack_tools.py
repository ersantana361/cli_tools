import os
import re
from typing import Optional
from rich.console import Console
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from smolagents import tool

@tool
def parse_slack_link(slack_link: str) -> dict:
    """
    Extracts channel ID and thread timestamp from a Slack thread URL.

    Args:
        slack_link (str): The URL of the Slack thread to parse.
            Format: https://.../archives/{channel_id}/p{timestamp}

    Returns:
        dict: Dictionary containing:
            - channel_id (str): Slack channel ID
            - thread_ts (str): Thread timestamp (seconds.microseconds format)
    """
    match = re.search(
        r'slack\.com/archives/(?P<channel_id>[A-Z0-9]+)/p(?P<thread_ts_url>\d+)',
        slack_link
    )
    if not match:
        raise ValueError(f"Invalid Slack thread URL: {slack_link}")
    
    channel_id = match.group("channel_id")
    thread_ts_url = match.group("thread_ts_url")

    if len(thread_ts_url) < 10:
        raise ValueError(f"Invalid timestamp in URL: {thread_ts_url}")

    seconds = thread_ts_url[:10]
    microseconds = thread_ts_url[10:16].ljust(6, '0')
    
    return {
        "channel_id": channel_id,
        "thread_ts": f"{seconds}.{microseconds}"
    }

@tool
def format_for_slack(content: str, target: str = "analysis") -> str:
    """
    Converts markdown to Slack-compatible formatting.
    
    Args:
        content (str): Markdown-formatted text to convert
        target (str): Content type ("analysis" or "pr_report")
    
    Returns:
        str: Slack-formatted text
    """
    # Header conversion
    content = re.sub(r'^#+\s+(.*)$', r'*\1*', content, flags=re.MULTILINE)
    
    # Bold/italic conversion
    content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
    content = re.sub(r'__(.*?)__', r'_\1_', content)
    
    # List conversion
    content = re.sub(r'^-\s+(.*)$', r'• \1', content, flags=re.MULTILINE)
    
    # Code blocks preservation
    content = re.sub(r'```(.*?)```', r'```\1```', content, flags=re.DOTALL)
    
    # Link handling
    if target == "pr_report":
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<\2|\1>', content)
    else:
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
    
    return content.strip()

@tool
def post_to_slack(
    content: str,
    slack_link: str,
    title: Optional[str] = None,
    content_type: str = "analysis"
) -> dict:
    """
    Posts formatted content to a Slack thread.

    Args:
        content (str): Text content to post (markdown format)
        slack_link (str): Slack thread URL
        title (Optional[str]): Optional title for the message
        content_type (str): Content type ("analysis" or "pr_report")

    Returns:
        dict: Result dictionary containing:
            - channel (str): Channel ID
            - thread_ts (str): Thread timestamp
            - message_ts (str): Message timestamp
            - success (bool): Operation status
            - error (str): Optional error message
    """
    console = Console()
    try:
        link_info = parse_slack_link(slack_link)
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        formatted_content = format_for_slack(content, content_type)
        if title:
            formatted_content = f"*{title}*\n\n{formatted_content}"

        response = client.chat_postMessage(
            channel=link_info["channel_id"],
            text=formatted_content,
            thread_ts=link_info["thread_ts"]
        )
        
        console.print(f"[green]✅ Posted to thread in channel {link_info['channel_id']}[/green]")
        return {
            "channel": link_info["channel_id"],
            "thread_ts": link_info["thread_ts"],
            "message_ts": response["ts"],
            "success": True
        }

    except SlackApiError as e:
        error_msg = f"Slack API Error: {e.response['error']}"
        console.print(f"[red]🚫 {error_msg}[/red]")
        return {"error": error_msg, "success": False}
    except Exception as e:
        console.print(f"[red]🚫 Error: {str(e)}[/red]")
        return {"error": str(e), "success": False}
