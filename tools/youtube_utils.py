import os
import re
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
