import re
import os
import requests
import tempfile
from prompt import client, generate
from moviepy.editor import VideoFileClip
from response_model import ResponseModel, ContentModel
from fastapi.exceptions import HTTPException 
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import html

load_dotenv()

FILENAME = "temp_audio"
CLIPPED_AUDIO_FILENAME = "temp_audio_clipped"

def process_youtube_links(video_url : str):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_video_file = rapid_api(video_url, temp_dir)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error downloading audio: {e}")
        
        video_clip = VideoFileClip(temp_video_file)

        if video_clip.duration > 240:
            video_clip = video_clip.subclip(0, 240)

        audio_clip = video_clip.audio
        clipped_audio_file_path = os.path.join(temp_dir, f"{CLIPPED_AUDIO_FILENAME}.mp3")
        audio_clip.write_audiofile(clipped_audio_file_path)

        audio_clip.close()
        video_clip.close()

        try:
            with open(clipped_audio_file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,  
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {e}")
        
        text_content = transcription.text
        categories = generate(text_content)
        return ResponseModel(status=True, message="Categories extracted successfully", url=video_url, content=ContentModel(category_report=categories))

def get_video_id(url):
    watch_pattern = r"(?:youtube\.com\/watch\?v=)([\w-]+)"
    shorts_pattern = r"(?:youtube\.com\/shorts\/)([\w-]+)"

    watch_match = re.search(watch_pattern, url)
    if watch_match:
        return watch_match.group(1)

    shorts_match = re.search(shorts_pattern, url)
    if shorts_match:
        return shorts_match.group(1)

    raise HTTPException(status_code=400, detail="Invalid YouTube URL")

def sanitize_filename(title):
    valid_filename = re.sub(r'[<>:"/\\|?*]', '', title)
    valid_filename = valid_filename[:255]
    return valid_filename

def rapid_api(video_url, temp_dir=os.getcwd()):
    video_id = get_video_id(video_url)

    API_URL = os.getenv("RAPID_API_URL")
    if not API_URL:
        raise HTTPException(status_code=500, detail="Missing RAPID_API_URL in environment variables")

    headers = {
        "X-RapidAPI-Key": os.getenv("X-RapidAPI-Key")
    }
    if not headers["X-RapidAPI-Key"]:
        raise HTTPException(status_code=500, detail="Missing X-RapidAPI-Key in environment variables")
    
    response = requests.get(API_URL, params={'id': video_id}, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error occurred: {response.content}")
    
    data = response.json()
    sanitized_title = sanitize_filename(data['title'])
    FILE_NAME = f"{sanitized_title}.mp4"
    FILE_PATH = os.path.join(temp_dir, FILE_NAME)

    video = requests.get(data['formats'][0]['url'])
    if video.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to download video")
    
    with open(FILE_PATH, 'wb') as o:
        o.write(video.content)
    
    return FILE_PATH

def get_video_transcript(video_id: str):
    url = "https://youtubetranscript.com/"
    response = requests.get(url, params={'server_vid2': video_id})
    if not response.text:
        raise HTTPException(status_code=500, detail="Transcript not retrieved")
    
    try:
        root = ET.fromstring(response.text)
        transcript = [html.unescape(text_element.text) for text_element in root.findall('text')]
        return " ".join(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing transcript: {e}")

def process_youtube_url(video_url):
    try:
        video_id = get_video_id(video_url)
        transcript = get_video_transcript(video_id)
        categories = generate(transcript)
        return ResponseModel(status=True, message="Categories extracted successfully", url=video_url, content=ContentModel(category_report=categories))
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.detail)
    
if __name__ == "__main__":
    response = process_youtube_url("https://youtubetranscript.com/?v=hnlz0YYCpBU")
    print('done')
