import os
import tempfile
import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from prompt import generate, client
from moviepy.editor import VideoFileClip
from response_model import ResponseModel, ContentModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_processing import FILENAME, CLIPPED_AUDIO_FILENAME

# _______________________Fetch HTML content from the URL and extract text___________________________________________

def fetch_and_extract_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        return text_content
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

#___________________________ Function to handle URL categories___________________________________________________________

def categories_url(url):
    try:
        text_content = fetch_and_extract_text(url)
        if not text_content:
            raise HTTPException(status_code=400, detail="Failed to fetch or extract text from the URL")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=1000)
        chunks = text_splitter.create_documents([text_content])
        categories = generate(chunks[0].page_content)
        
        return ResponseModel(status=True, message="Categories extracted successfully", url=url, content=ContentModel(category_report=categories))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in categories_url: {e}")

# _______________________ Process Video Source URL ___________________________________________

def process_video_source_url(url):
    try:
        print("Downloading video")
        file_extension = os.path.splitext(url)[-1]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = os.path.join(temp_dir, f"{FILENAME}{file_extension}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as video_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        video_file.write(chunk)
            
            print("Video file downloaded successfully")
            
            video = VideoFileClip(save_path)
            audio = video.audio
            if audio.duration > 240:
                audio = audio.subclip(0, 240)
            
            clipped_audio_file_path = os.path.join(temp_dir, f"{CLIPPED_AUDIO_FILENAME}.mp3")
            print("Writing audio file")
            audio.write_audiofile(clipped_audio_file_path)
            
            audio.close()
            video.close()
            
            with open(clipped_audio_file_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,  
                )
            
            text_content = transcription.text
            categories = generate(text_content)
            return ResponseModel(status=True, message="Categories extracted successfully", url=url, content=ContentModel(category_report=categories))
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=f"HTTP Error while downloading video: {e}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error while downloading video: {e}")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"File handling error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in process_video_source_url: {e}")
