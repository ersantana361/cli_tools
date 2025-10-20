import os
import re
from typing import List, Optional
from googleapiclient.discovery import build

def extract_video_id(url: str) -> str:
    """
    Extracts the video ID from a YouTube URL or a direct ID.
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def extract_playlist_id(url: str) -> Optional[str]:
    """
    Extracts the playlist ID from a YouTube playlist URL.

    Args:
        url: YouTube playlist URL

    Returns:
        Playlist ID or None if not found
    """
    patterns = [
        r'[?&]list=([0-9A-Za-z_-]+)',
        r'youtube\.com/playlist\?list=([0-9A-Za-z_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_playlist_url(url: str) -> bool:
    """
    Checks if a URL is a YouTube playlist URL.

    Args:
        url: URL to check

    Returns:
        True if URL contains playlist parameter
    """
    return 'list=' in url or 'playlist?' in url

def extract_playlist_videos(playlist_url: str, max_results: int = 50) -> List[str]:
    """
    Extracts all video URLs from a YouTube playlist.

    Args:
        playlist_url: YouTube playlist URL
        max_results: Maximum number of videos to fetch per API call (default: 50)

    Returns:
        List of video URLs in the format https://youtu.be/VIDEO_ID

    Raises:
        Exception: If YOUTUBE_API_KEY is missing or API call fails
    """
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    if not YOUTUBE_API_KEY:
        raise Exception("Missing YOUTUBE_API_KEY environment variable")

    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError(f"Could not extract playlist ID from URL: {playlist_url}")

    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        video_urls = []
        next_page_token = None

        while True:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=max_results,
                pageToken=next_page_token
            )
            response = request.execute()

            # Extract video IDs and convert to URLs
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_urls.append(f"https://youtu.be/{video_id}")

            # Check if there are more pages
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return video_urls

    except Exception as e:
        raise Exception(f"Failed to fetch playlist videos: {e}")

def get_video_title(video_id: str) -> str:
    """
    Fetches the video title using the YouTube API.
    """
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    if not YOUTUBE_API_KEY:
        raise Exception("Missing YOUTUBE_API_KEY environment variable")
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        return response['items'][0]['snippet']['title']
    except Exception as e:
        print(f"Could not fetch title: {e}")
        return "Untitled Video"

def format_time(seconds_float: float) -> str:
    """
    Formats a number of seconds (float) into MM:SS format.
    """
    seconds = int(seconds_float)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"
