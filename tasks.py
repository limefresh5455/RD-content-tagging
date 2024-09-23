import requests
import concurrent.futures
from fastapi import UploadFile
from utils import process_url_with_retry, process_file_with_retry

def send_callback(data, callback_url):
    requests.post(callback_url, json=data)

def process_files(request_id : str, files : list[UploadFile], callback_url : str):
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

    callback_data = {'reqeust_id' : request_id, 'data' : results}
    send_callback(data = callback_data, callback_url=callback_url)
    print("background task completed")

def process_urls(request_id : str, urls : list[str], callback_url : str):
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

    callback_data = {'request_id' : request_id, 'data' : results}
    send_callback(data=callback_data, callback_url=callback_url)
    print("background task completed")