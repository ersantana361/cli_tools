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
    Converts markdown to clean Slack formatting with strict style rules.

    Args:
        content (str): Markdown content to convert
        target (str): Content type ("analysis" or "pr_report")

    Returns:
        str: Properly formatted Slack text
    """
    # Convert headers to bold (any # level)
    content = re.sub(r'^#+\s+(.*?)(\s*#+)?$', r'*\1*', content, flags=re.MULTILINE)
    
    # Convert bold/italic to Slack format
    content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
    content = re.sub(r'__(.*?)__', r'_\1_', content)
    
    # Convert lists to bullet points with proper indentation
    content = re.sub(r'^(\s*)-\s+(.*)$', r'\1• \2', content, flags=re.MULTILINE)
    
    # Remove markdown links while preserving text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # Remove horizontal rules and section dividers
    content = re.sub(r'-{3,}', '', content)
    
    # Clean up whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 newlines
    content = re.sub(r'[ \t]+', ' ', content)     # Remove extra spaces
    content = re.sub(r'\n\s*\n', '\n\n', content) # Clean empty lines
    
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
        # Try multiple token environment variables
        slack_token = os.getenv("SLACK_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise Exception("Slack token not found. Set SLACK_TOKEN or SLACK_BOT_TOKEN environment variable.")
        
        client = WebClient(token=slack_token)
        
        # Apply final formatting
        formatted_content = format_for_slack(content, content_type)
        
        # Add title if provided (already formatted as bold)
        if title:
            formatted_content = f"*{title}*\n\n{formatted_content}"
            
        # Remove any remaining URLs
        formatted_content = re.sub(r'https?://\S+', '', formatted_content)

        response = client.chat_postMessage(
            channel=link_info["channel_id"],
            text=formatted_content,
            thread_ts=link_info["thread_ts"]
        )
        
        # Don't print success here - let the caller handle success/failure messaging
        return {
            "channel": link_info["channel_id"],
            "thread_ts": link_info["thread_ts"],
            "message_ts": response["ts"],
            "success": True
        }

    except SlackApiError as e:
        error_details = e.response.get('error', 'unknown_error')
        if error_details == 'channel_not_found':
            error_msg = f"Slack API Error: {error_details} - Check if bot has access to channel {link_info.get('channel_id', 'unknown')}"
        elif error_details == 'not_authed':
            error_msg = f"Slack API Error: {error_details} - Check SLACK_TOKEN environment variable"
        else:
            error_msg = f"Slack API Error: {error_details}"
        console.print(f"[red]🚫 {error_msg}[/red]")
        return {"error": error_msg, "success": False}
    except Exception as e:
        console.print(f"[red]🚫 Error: {str(e)}[/red]")
        return {"error": str(e), "success": False}
