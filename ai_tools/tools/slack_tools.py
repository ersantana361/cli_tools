import os
import re
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from smolagents import tool

def check_slack_bot_permissions() -> dict:
    """
    Check current Slack bot permissions and provide diagnostic information.
    
    Returns:
        dict: Information about bot permissions and access
    """
    console = Console()
    slack_token = os.getenv("SLACK_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
    
    if not slack_token:
        return {"error": "No Slack token found", "suggestions": ["Set SLACK_TOKEN environment variable"]}
    
    try:
        client = WebClient(token=slack_token)
        auth_response = client.auth_test()
        
        # Try to get bot info
        try:
            bot_info = client.bots_info(bot=auth_response["user_id"])
            bot_name = bot_info["bot"]["name"]
        except:
            bot_name = auth_response.get("user", "unknown")
        
        return {
            "success": True,
            "bot_name": bot_name,
            "user_id": auth_response["user_id"],
            "team": auth_response.get("team", "unknown"),
            "suggestions": [
                f"Bot '{bot_name}' is authenticated",
                "To add bot to channel: /invite @" + bot_name,
                "Required scopes: channels:read, channels:history"
            ]
        }
        
    except SlackApiError as e:
        return {
            "error": f"Slack API Error: {e.response['error']}",
            "suggestions": ["Check SLACK_TOKEN value", "Verify bot OAuth scopes"]
        }
    except Exception as e:
        return {
            "error": f"Error: {str(e)}",
            "suggestions": ["Check network connection", "Verify SLACK_TOKEN format"]
        }

@tool
def extract_youtube_from_slack_channel(channel_name: str) -> Optional[str]:
    """
    Extracts the first YouTube URL found in the latest message of a Slack channel.
    
    Args:
        channel_name (str): The name of the Slack channel (e.g., "erick-chatbot-room")
    
    Returns:
        Optional[str]: First YouTube URL found in the latest message, or None if no YouTube link found
    """
    console = Console()
    try:
        slack_token = os.getenv("SLACK_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise Exception("Slack token not found. Set SLACK_TOKEN or SLACK_BOT_TOKEN environment variable.")
        
        client = WebClient(token=slack_token)
        
        # Debug: Show what we're looking for
        console.print(f"[dim]Looking for channel: '{channel_name}'[/dim]")
        
        # Find the channel by name - try multiple approaches
        channels_response = client.conversations_list(
            types="public_channel,private_channel,mpim,im", 
            limit=200
        )
        
        console.print(f"[dim]Found {len(channels_response['channels'])} total channels[/dim]")
        
        target_channel = None
        all_channels = []
        accessible_channels = []
        
        for channel in channels_response["channels"]:
            all_channels.append(f"{channel['name']} (member: {channel.get('is_member', 'unknown')})")
            
            # Check multiple conditions for membership
            is_member = (
                channel.get("is_member", False) or 
                not channel.get("is_archived", False)  # Sometimes is_member isn't set correctly
            )
            
            if is_member:
                accessible_channels.append(channel["name"])
            
            if channel["name"] == channel_name:
                console.print(f"[dim]Found matching channel: {channel['name']}, is_member: {channel.get('is_member', 'unknown')}[/dim]")
                if is_member:
                    target_channel = channel
                    break
        
        console.print(f"[dim]Total channels checked: {len(all_channels)}[/dim]")
        console.print(f"[dim]Accessible channels found: {len(accessible_channels)}[/dim]")
        
        if not target_channel:
            # Show available channels in a nice panel
            from rich.panel import Panel
            from rich.columns import Columns
            from rich.text import Text
            
            if accessible_channels:
                channel_list = [f"• {ch}" for ch in accessible_channels[:10]]  # Show first 10
                console.print(Panel(
                    "\n".join(channel_list),
                    title=f"[bold cyan]📋 Available Channels ({len(accessible_channels)} total)[/bold cyan]",
                    border_style="cyan"
                ))
                raise Exception(f"Channel '{channel_name}' not found. Available channels: {', '.join(accessible_channels)}")
            else:
                debug_list = [f"• {ch}" for ch in all_channels[:8]]  # Show first 8 for debugging
                console.print(Panel(
                    "\n".join(debug_list),
                    title="[bold yellow]🔍 Debug: All Channels Found[/bold yellow]",
                    border_style="yellow"
                ))
                raise Exception("Bot appears to have no channel access. Check bot permissions and OAuth scopes.")
        
        console.print(f"[green]✅ Found channel: {channel_name} ({target_channel['id']})[/green]")
        
        # Get the latest message from the channel - try multiple approaches
        response = None
        
        # First try: regular conversations_history
        try:
            response = client.conversations_history(
                channel=target_channel["id"],
                limit=1
            )
            console.print(f"[green]✅ Successfully read channel history[/green]")
        except SlackApiError as e:
            if e.response.get('error') == 'not_in_channel':
                console.print(f"[yellow]⚠️ not_in_channel error - trying alternative approach[/yellow]")
                
                # Alternative: try to use the actual channel ID directly (bypass is_member check)
                try:
                    # Force try with the channel ID we found
                    response = client.conversations_history(
                        channel=target_channel["id"], 
                        limit=1
                    )
                    console.print(f"[green]✅ Direct channel access worked[/green]")
                except SlackApiError as direct_error:
                    console.print(f"[yellow]⚠️ Channel history access failed: {direct_error.response.get('error')}[/yellow]")
                    console.print("[cyan]💡 Bot can be in the channel but lack message reading permissions[/cyan]")
                    
                    # Interactive prompt instead of error
                    should_input_manually = Confirm.ask(
                        "[bold cyan]Would you like to manually provide the YouTube URL instead?[/bold cyan]",
                        console=console,
                        default=True
                    )
                    
                    if should_input_manually:
                        return "MANUAL_INPUT_REQUESTED"  # Special return value to trigger manual input
                    else:
                        console.print("[dim]Operation cancelled by user[/dim]")
                        return None
            else:
                raise e
        
        if not response["messages"]:
            raise Exception(f"No messages found in channel '{channel_name}'")
        
        message = response["messages"][0]
        text = message.get("text", "")
        console.print(f"[dim]Latest message: {text[:100]}...[/dim]")
        
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                console.print(f"[green]✅ Found YouTube URL: {youtube_url}[/green]")
                return youtube_url
        
        return None
        
    except SlackApiError as e:
        error_details = e.response.get('error', 'unknown_error')
        console.print(f"[red]🚫 Slack API Error: {error_details}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]🚫 Error: {str(e)}[/red]")
        return None

@tool
def list_accessible_slack_channels() -> list:
    """
    List all Slack channels the bot has access to.
    
    Returns:
        list: List of dictionaries with channel info (name, id, is_member)
    """
    console = Console()
    try:
        slack_token = os.getenv("SLACK_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            console.print("[red]🚫 No Slack token found[/red]")
            return []
        
        client = WebClient(token=slack_token)
        
        channels_response = client.conversations_list(
            types="public_channel,private_channel",
            limit=200
        )
        
        accessible_channels = []
        console.print("[cyan]📋 Accessible Slack channels:[/cyan]")
        
        for channel in channels_response["channels"]:
            if channel["is_member"]:
                accessible_channels.append({
                    "name": channel["name"],
                    "id": channel["id"],
                    "is_member": True
                })
                console.print(f"  • {channel['name']} ({channel['id']})")
        
        if not accessible_channels:
            console.print("[yellow]⚠️ No accessible channels found[/yellow]")
        
        return accessible_channels
        
    except SlackApiError as e:
        console.print(f"[red]🚫 Slack API Error: {e.response.get('error', 'unknown')}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]🚫 Error: {str(e)}[/red]")
        return []

@tool
def extract_youtube_from_slack_thread(slack_link: str) -> Optional[str]:
    """
    Extracts the first YouTube URL found in the main Slack message (not thread replies).
    
    Args:
        slack_link (str): The URL of the Slack message to search.
            Format: https://.../archives/{channel_id}/p{timestamp}
    
    Returns:
        Optional[str]: First YouTube URL found in the main message, or None if no YouTube link found
    """
    console = Console()
    try:
        link_info = parse_slack_link(slack_link)
        slack_token = os.getenv("SLACK_TOKEN") or os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise Exception("Slack token not found. Set SLACK_TOKEN or SLACK_BOT_TOKEN environment variable.")
        
        client = WebClient(token=slack_token)
        
        # Show bot info for debugging
        bot_info = check_slack_bot_permissions()
        if bot_info.get("success"):
            console.print(f"[dim]Bot: {bot_info['bot_name']} ({bot_info['user_id']})[/dim]")
        else:
            console.print(f"[yellow]⚠️ Bot check: {bot_info.get('error', 'unknown')}[/yellow]")
        
        # Debug: Show which channel we're trying to access
        console.print(f"[dim]Trying to access channel: {link_info['channel_id']}[/dim]")
        
        # Debug: List accessible channels
        try:
            channels_response = client.conversations_list(types="public_channel,private_channel", limit=100)
            accessible_channels = [f"{ch['name']} ({ch['id']})" for ch in channels_response["channels"] if ch["is_member"]]
            console.print(f"[dim]Accessible channels: {', '.join(accessible_channels)}[/dim]")
        except:
            pass
        
        # Try to read the message directly first
        response = None
        target_channel = link_info["channel_id"]
        
        try:
            # First attempt: try conversations.replies (works better with thread posting permissions)
            console.print(f"[dim]Trying conversations.replies for thread access...[/dim]")
            response = client.conversations_replies(
                channel=target_channel,
                ts=link_info["thread_ts"],
                limit=1,
                inclusive=True
            )
            console.print(f"[green]✅ Successfully used conversations.replies[/green]")
        except SlackApiError as replies_error:
            console.print(f"[yellow]⚠️ conversations.replies failed: {replies_error.response.get('error')}[/yellow]")
            # Fallback to conversations.history
            try:
                console.print(f"[dim]Trying conversations.history fallback...[/dim]")
                response = client.conversations_history(
                    channel=target_channel,
                    latest=link_info["thread_ts"],
                    oldest=link_info["thread_ts"],
                    inclusive=True,
                    limit=1
                )
                console.print(f"[green]✅ Successfully used conversations.history[/green]")
            except SlackApiError as history_error:
                console.print(f"[red]🚫 conversations.history also failed: {history_error.response.get('error')}[/red]")
                raise history_error  # Re-raise to trigger fallback logic
        
            # If we got here, one of the methods worked
            if response:
                # Check if we have access to channel info for display
                try:
                    channel_info = client.conversations_info(channel=target_channel)
                    console.print(f"[green]✅ Reading from channel: {channel_info['channel']['name']}[/green]")
                except:
                    console.print(f"[green]✅ Reading from channel: {target_channel}[/green]")
                    
        except SlackApiError as e:
            if e.response['error'] in ['not_in_channel', 'channel_not_found']:
                console.print(f"[yellow]⚠️ Cannot access channel {target_channel} directly[/yellow]")
                
                # Fallback: try to find the message in accessible channels
                console.print("[cyan]🔄 Searching in accessible channels...[/cyan]")
                
                try:
                    # Get list of channels the bot has access to
                    channels_response = client.conversations_list(
                        types="public_channel,private_channel",
                        limit=100
                    )
                    
                    for channel in channels_response["channels"]:
                        if channel["is_member"]:
                            console.print(f"[dim]  Checking channel: {channel['name']} ({channel['id']})[/dim]")
                            try:
                                fallback_response = client.conversations_history(
                                    channel=channel["id"],
                                    latest=link_info["thread_ts"],
                                    oldest=link_info["thread_ts"],
                                    inclusive=True,
                                    limit=1
                                )
                                console.print(f"[dim]  Found {len(fallback_response.get('messages', []))} messages[/dim]")
                                if fallback_response["messages"]:
                                    response = fallback_response
                                    target_channel = channel["id"]
                                    console.print(f"[green]✅ Found message in channel: {channel['name']}[/green]")
                                    break
                            except SlackApiError as search_error:
                                console.print(f"[dim]  Error in {channel['name']}: {search_error.response.get('error', 'unknown')}[/dim]")
                                continue  # Try next channel
                                
                except SlackApiError:
                    pass  # Fallback failed, will raise original error below
                    
                if not response:
                    raise Exception(f"Cannot read messages from channel {link_info['channel_id']}. Bot may have thread access but not channel history permissions.")
            else:
                raise Exception(f"Cannot access channel {target_channel}: {e.response['error']}")
        
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        # Check only the main message (should be exactly one message)
        if response["messages"]:
            message = response["messages"][0]
            text = message.get("text", "")
            for pattern in youtube_patterns:
                match = re.search(pattern, text)
                if match:
                    video_id = match.group(1)
                    return f"https://www.youtube.com/watch?v={video_id}"
        
        return None
        
    except SlackApiError as e:
        error_details = e.response.get('error', 'unknown_error')
        if error_details == 'not_in_channel':
            console.print(f"[yellow]⚠️ Bot cannot read channel history for {link_info.get('channel_id', 'unknown')}[/yellow]")
            console.print("[cyan]💡 The bot can post to threads but lacks permission to read channel messages[/cyan]")
            console.print("[dim]   This is common with thread-only bot access or limited OAuth scopes[/dim]")
            
            # Interactive prompt instead of error
            should_input_manually = Confirm.ask(
                "[bold cyan]Would you like to manually provide the YouTube URL instead?[/bold cyan]",
                console=console,
                default=True
            )
            
            if should_input_manually:
                return "MANUAL_INPUT_REQUESTED"  # Special return value to trigger manual input
            else:
                console.print("[dim]Operation cancelled by user[/dim]")
                return None
                
        elif error_details == 'channel_not_found':
            console.print(f"[red]🚫 Channel not found or bot doesn't have access[/red]")
            console.print("[yellow]💡 Check: Channel ID and bot permissions[/yellow]")
        elif error_details == 'missing_scope':
            console.print(f"[red]🚫 Bot missing required OAuth scopes[/red]")
            console.print("[yellow]💡 Required scopes: channels:read, channels:history[/yellow]")
        else:
            console.print(f"[red]🚫 Slack API Error: {error_details}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]🚫 Error: {str(e)}[/red]")
        return None

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
