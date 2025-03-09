import argparse
import os
from youtube_transcript_api import YouTubeTranscriptApi
import pyperclip
import re
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def get_video_title(video_id):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        return response['items'][0]['snippet']['title']
    except Exception as e:
        print(f"Could not fetch title: {e}")
        return "Untitled Video"

def format_time(seconds_float):
    seconds = int(seconds_float)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"

def fetch_transcript(video_url, language):
    try:
        video_id = extract_video_id(video_url)
        video_title = get_video_title(video_id)
        video_base_url = f"https://youtu.be/{video_id}"

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])

        transcript_entries = []
        for entry in transcript:
            start_time = entry['start']
            formatted_time = format_time(start_time)
            link = f"{video_base_url}?t={int(start_time)}"
            transcript_entries.append(f"{formatted_time} (Link: {link}): {entry['text']}")

        transcript_entries_text = "\n".join(transcript_entries)

        transcript_text = f"""
**Video Analysis Request**

Analyze this YouTube video transcript and structure your response as:

### **Introduction**
- **Title**: [{video_title}]({video_url})
- **Overview**:
  A comprehensive explanation of the video's core objectives, structural flow, and key conceptual arcs. Identify how major themes connect and evolve throughout the presentation.

---

### **Chronological Analysis**

For each significant segment in playback order:

#### **[Section Title]**
[Timestamp: XX:XX](link)
1-2 verbatim excerpts from the transcript showcasing critical content, formatted as:
> *"Exact quoted text from transcript"*

Detailed analysis containing:
- Technical explanation of concepts/arguments
- Contextualization within the broader video
- Significance to the overall subject matter
- Real-world implications or applications
- Connections to other segments/themes

---

### **Conclusion**
Synthesize the video's progression from initial concepts to final takeaways, emphasizing:
- Key intellectual milestones
- Practical/theoretical importance
- Overall learning outcomes

**Requirements**:
- Maintain strict chronological order with timestamps
- Use 3-7 substantial segments based on content density
- Blend direct quotes with deep technical analysis
- Explain specialized terms/concepts contextually
- Output language: {language}

YouTube Link: {video_url}

[TRANSCRIPT START]
{transcript_entries_text}
[TRANSCRIPT END]
"""

        pyperclip.copy(transcript_text)
        print("Transcript prompt copied to clipboard.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate video analysis prompt with transcript")
    parser.add_argument('video', help="YouTube video ID or URL")
    parser.add_argument('--language', default='en', help="Language code (default: en)")
    args = parser.parse_args()
    fetch_transcript(args.video, args.language)
