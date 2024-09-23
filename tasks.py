import requests
import concurrent.futures
from fastapi import UploadFile
from utils import process_url_with_retry, process_file_with_retry

def send_callback(results, callback_url):
    requests.post(callback_url, json=results)

def process_files(files : list[UploadFile], callback_url : str):
    print("background task running")
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file_with_retry, file): file for file in files}
        
        for future in concurrent.futures.as_completed(futures):
            file = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

    send_callback(results=results, callback_url=callback_url)
    print("background task completed")

def process_urls(urls: list[str], callback_url : str):
    print("background task running")
    urls_list = urls.split(',')
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_url_with_retry, url): url for url in urls_list}
        
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

    send_callback(results=results, callback_url=callback_url)
    print("background task completed")