import argparse
from youtube_transcript_api import YouTubeTranscriptApi
import pyperclip
import re

def extract_video_id(url_or_id):
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(video_id_pattern, url_or_id)
    if match:
        return match.group(1)
    return url_or_id

def fetch_transcript(video_url_or_id):
    try:
        video_id = extract_video_id(video_url_or_id)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = '\n'.join([entry['text'] for entry in transcript])
        pyperclip.copy(transcript_text)
        print("Transcript copied to clipboard.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch YouTube video transcript and copy it to clipboard.")
    parser.add_argument('video', help="YouTube video ID or URL")
    args = parser.parse_args()
    fetch_transcript(args.video)
