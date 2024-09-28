import os
import time
import PyPDF2
import tempfile
import requests
import urllib.parse
from pytube import YouTube
import moviepy.editor as mp
from pydantic import HttpUrl
from bs4 import BeautifulSoup
from fastapi import HTTPException
from urllib.parse import urlparse
from prompt import generate, generate_summary, client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_processing import process_youtube_links

MAX_RETRIES = int(os.getenv('MAX_RETRIES', 5))

# _______________________Fetch HTML content from the URL and extract text___________________________________________
def fetch_and_extract_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        return text_content
    except requests.RequestException as e:
        return 'sorry data could not be extracted'
#___________________________ Function to handle URL categories___________________________________________________________
def categories_url(url):
    text_content = fetch_and_extract_text(url)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=1000)
    chunks = text_splitter.create_documents([text_content])
    # print("chunks", chunks)
    categories = generate(chunks[0].page_content)
    return categories
# _________________________________Function to handle video to text conversion_________________________________________________
def video_to_text(file):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_file = os.path.join(temp_dir, "temp_video.mp4")
            temp_audio_file = os.path.join(temp_dir, "temp_audio.mp3")
            with open(temp_video_file, "wb") as temp_video:
                if isinstance(file, str):  # Check if file is a string
                    # If it's a string, assume it's the file path and open it for reading
                    with open(file, "rb") as f:
                        temp_video.write(f.read())
                else:
                    # If it's not a string, assume it's a file object and directly read from it
                    temp_video.write(file.file.read())  
            # Extract audio from video
            video_clip = mp.VideoFileClip(temp_video_file)
            video_duration = video_clip.duration
            # print(video_duration)
            if video_duration <240:
                pass
            else:
                video_clip = video_clip.subclip(0,240)

            audio_clip = video_clip.audio
            audio_clip.write_audiofile(temp_audio_file)
            audio_clip.close()
            video_clip.close()
            with open(temp_audio_file, "rb") as audio_file:
        # Transcribe audio using Whisper model
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,  
                )
            # print(transcription.text)
            text_content = transcription.text
            # print(text_content)
            report=generate(text_content)
            return report
    except Exception as e:
        return {"error": str(e)}
#____________________________________Function to handle PDF file categories______________________________________________
def document_categorieser(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file.file)
        text = ""
        num_pages = len(reader.pages)
        for page_number in range(num_pages):
            text += reader.pages[page_number].extract_text()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=1000)
        chunks = text_splitter.create_documents([text])
        # Generate category report for the first chunk
        category_report = generate(chunks[0].page_content)
        # Generate summary for each chunk and combine them
        summaries = [generate_summary(chunk.page_content) for chunk in chunks]
        final_summary = " ".join(summaries)
        all_summary=generate_summary(final_summary)
        return {"category_report": category_report, "summary": all_summary}
    except Exception as e:
        return {"error": str(e)}
# __________________________________________Function to handle YouTube video link______________________________________________
def youtube_video_to_text(video_url):
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
        output_directory = "Temporary_Video"
        os.makedirs(output_directory, exist_ok=True)
        video_file_path = os.path.join(output_directory, "temp_video.mp4")
        file = video_stream.download(output_path=output_directory, filename="temp_video.mp4")
        return video_to_text(file)
       
    except Exception as e:
        return {"error": str(e)}
# _____________________________________________Function to process each URL  asynchronously_________________________________
def process_url(url):
    url= urllib.parse.unquote_plus(url) 
    
    if url:
        if (urlparse(url).scheme in ['http', 'https'])and urlparse(url).netloc != 'www.youtube.com' :
            return categories_url(url)
        elif (urlparse(url).scheme in ['http', 'https']) and urlparse(url).netloc == 'www.youtube.com':
            return process_youtube_links(url)
        else:
            raise HTTPException(status_code=400, detail='Unsupported URL format')
        
    else:
        raise HTTPException(status_code=400, detail='Please provide either a file or a URL.')


#____________________________________________ Function to process each URL  asynchronously________________________________
def process_file(file):
    filename = file.filename
    extension = os.path.splitext(filename)[1].lower()

    if extension == '.pdf':
        return document_categorieser(file)
    elif extension in ['.mp4', '.mov', '.avi', 'wav']:
        return video_to_text(file)
    else:
        raise HTTPException(status_code=400, detail='Invalid input type')
#______________________________max_retry_for_openai_rateLINIT_Error_for_file______________________________________________
def process_file_with_retry(file):
    # MAX_RETRIES = 5
    retries = 0
    while retries < MAX_RETRIES:
        try:
            result = process_file(file)
            if "error" in result:
                if "rate_limit_exceeded" in result["error"]:
                    print(f"Rate limit exceeded for {file.filename}. Waiting for 5 seconds before retrying...")
                    time.sleep(10)
                else:
                    print(f"Retry {retries+1}/{MAX_RETRIES} for {file.filename}: {result['error']}")
                    retries += 1
                    time.sleep(2 ** retries)
            else:
                return result
        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                print(f"Rate limit exceeded for {file.filename}. Waiting for 5 seconds before retrying...")
                time.sleep(10)
            else:
                print(f"Retry {retries+1}/{MAX_RETRIES} for {file.filename}: {e}")
                retries += 1
                time.sleep(2 ** retries)
    return {"error": f"Failed to process {file.filename} after {MAX_RETRIES} retries"}
#______________________________max_retry_for_openai_rateLINIT_Error_for_url______________________________________________

def process_url_with_retry(url):
    # MAX_RETRIES = 5
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return process_url(url)
        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                print(f"Rate limit exceeded for {url}. Waiting for 5 seconds before retrying...")
                time.sleep(10) 
            else:
                print(f"Retry {retries+1}/{MAX_RETRIES} for {url}: {e}")
                retries += 1
                time.sleep(2 ** retries) 
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Failed to process {url} after {MAX_RETRIES} retries"}