import re
import os
import time
import urllib.parse
from urllib.parse import urlparse
from video_processing import video_to_text
from fastapi import HTTPException, UploadFile
from youtube_processing import process_youtube_links
from url_processing import categories_url, process_video_source_url
from file_processing import document_categorieser, process_file_source_url
from response_model import URLCategoryModel, FileCategoryModel

MAX_RETRIES = int(os.getenv('MAX_RETRIES', 5))

def is_valid_pdf_url(url: str) -> bool:
    # Regular expression to check if the URL ends with ".pdf"
    pdf_pattern = r'.*\/.*\.pdf$'
    
    # Use re.match to validate the URL pattern
    if re.match(pdf_pattern, url):
        return True
    return False

def is_video_source_url(url : str):
    video_pattern = r'.*\.(mp4|avi|mkv|mov|wmv|flv|webm|mpeg|mpg|m4v)$'
    if re.match(video_pattern, url, re.IGNORECASE):
        return True
    return False
# _____________________________________________Function to process each URL  asynchronously_________________________________
def process_url(url):
    url= urllib.parse.unquote_plus(url)
    parsed_url =  urlparse(url)
    
    if url:
        if is_valid_pdf_url(url):
            return process_file_source_url(url)
        elif is_video_source_url(url):
            return process_video_source_url(url)
        elif (parsed_url.scheme in ['http', 'https'])and parsed_url.netloc != 'www.youtube.com' :
            return categories_url(url)
        elif (parsed_url.scheme in ['http', 'https']) and parsed_url.netloc == 'www.youtube.com':
            return process_youtube_links(url)
        else:
            raise HTTPException(status_code=400, detail='Unsupported URL format')
        
    else:
        raise HTTPException(status_code=400, detail='Please provide either a file or a URL.')


#____________________________________________ Function to process each URL  asynchronously________________________________
def process_file(file : UploadFile):
    filename = file.filename
    extension = os.path.splitext(filename)[1].lower()

    if extension == '.pdf':
        return document_categorieser(file)
    elif extension in ['.mp4', '.mov', '.avi', 'wav']:
        return video_to_text(file)
    else:
        raise HTTPException(status_code=400, detail='Invalid input type')
#______________________________max_retry_for_openai_rateLINIT_Error_for_file______________________________________________
def process_file_with_retry(file : UploadFile):
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
    # return {"error": f"Failed to process {file.filename} after {MAX_RETRIES} retries"}
    return FileCategoryModel(status= False, message=f"Failed to process {file.filename} after {MAX_RETRIES} retries", filename = file.filename, content = {})

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
    # return {"error": f"Failed to process {url} after {MAX_RETRIES} retries"}
    return URLCategoryModel(status=False, message = f"Failed to process {url} after {MAX_RETRIES} retries", url= url,content={})