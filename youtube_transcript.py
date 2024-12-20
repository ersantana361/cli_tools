import argparse
from youtube_transcript_api import YouTubeTranscriptApi
import pyperclip
import re

def extract_video_id(url):
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(video_id_pattern, url)
    if match:
        return match.group(1)
    return url

def fetch_transcript(video_url, language):
    try:
        video_id = extract_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])

        transcript_entries = "\n".join([f"{entry['start']}: {entry['text']}" for entry in transcript])

        transcript_text = f"""
Give me a summary from this transcript taken from a youtube video

Please analyze the following transcript and provide:
1. A **summary** of the main ideas discussed in the transcript.
2. A set of **bullet points** summarizing the general themes or arguments presented.
3. **Key excerpts with clickable timestamps** that highlight important points or arguments, with links to the respective moments in the video.

Youtube Link: {video_url}

Make sure the language used is: {language}.
Do not add any additional comments, context, or summaries outside the requested output.

[TRANSCRIPT START]
{transcript_entries}
[TRANSCRIPT END]
"""

        pyperclip.copy(transcript_text)
        print("Transcript copied to clipboard.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch YouTube video transcript and copy it to clipboard.")
    parser.add_argument('video', help="YouTube video ID or URL")
    parser.add_argument('--language', default='en', help="Language code for the transcript (default: en)")
    args = parser.parse_args()
    fetch_transcript(args.video, args.language)
