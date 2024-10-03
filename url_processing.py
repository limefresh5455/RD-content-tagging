import os
import tempfile
import requests
from bs4 import BeautifulSoup
from prompt import generate, client
from moviepy.editor import VideoFileClip
from response_model import URLCategoryModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_processing import FILENAME, CLIPPED_AUDIO_FILENAME

# _______________________Fetch HTML content from the URL and extract text___________________________________________

def fetch_and_extract_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        return text_content
    except requests.RequestException as e:
        return None
    
#___________________________ Function to handle URL categories___________________________________________________________

def categories_url(url):
    text_content = fetch_and_extract_text(url)
    if not text_content:
        return URLCategoryModel(status=False, message = "Failed to fetch or extract text from the URL", url=url,content=[])
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=1000)
    chunks = text_splitter.create_documents([text_content])
    # print("chunks", chunks)
    categories = generate(chunks[0].page_content)
    # return categories
    return URLCategoryModel(status=True, message = "Categories extracted successfully", url=url, content=categories)

def process_video_source_url(url):
    print("downloading video")
    file_extension = os.path.splitext(url)[-1]

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = os.path.join(temp_dir, f"{FILENAME}{file_extension}")
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as video_file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            video_file.write(chunk)
                
                video_file.close()
                print("Video file downloaded successfully")
            else:
                print("Failed to download Video")
                return None
            
            video = VideoFileClip(save_path)
            audio = video.audio
            if audio.duration > 240:
                audio.subclip(0,240)
            
            clipped_audio_file_path = os.path.join(temp_dir, f"{CLIPPED_AUDIO_FILENAME}.mp3")
            print("writing audio file")            
            audio.write_audiofile(clipped_audio_file_path)

            audio.close()
            video.close()
            
            with open(clipped_audio_file_path, "rb") as audio_file:
                    # Transcribe audio using Whisper model
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file,  
                    )
            
            text_content = transcription.text
            categories = generate(text_content)
            return URLCategoryModel(status=True, message = "Categories extracted successfully", url=url, content=categories)
    
    except Exception as e:
        print("Excpetion occured : ", e)
        return URLCategoryModel(status=False, message = f"Failed to fetch or extract text from the URL {e}", url= url,content=[])