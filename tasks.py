import requests
from fastapi import UploadFile, HTTPException
from response_model import CallbackResponseModel
from utils import process_file, process_url

def send_callback(data: CallbackResponseModel, callback_url: str):
    try:
        res = requests.post(callback_url, json=data.model_dump(mode='json'))
        res.raise_for_status()
        print("Status code:", res.status_code)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send callback: {str(e)}")

def process_files(request_id: str, files: list[UploadFile], callback_url: str):
    try:
        print("Background task running")
        
        results = []
        for file in files:
            try:
                result = process_file(file)
                results.append(result)
            except Exception as e:
                results.append({"file": file.filename, "error": str(e)})
                print(f"Error processing file {file.filename}: {e}")
        
        callback_data = CallbackResponseModel(request_id=request_id, data=results)
        send_callback(data=callback_data, callback_url=callback_url)
        print("Background task completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

def process_urls(request_id: str, urls: str, callback_url: str):
    try:
        print("Background task running")
        urls_list = urls.split(',')
        
        results = []
        for url in urls_list:
            try:
                result = process_url(url)
                results.append(result)
            except Exception as e:
                results.append({"url": url, "error": str(e)})
                print(f"Error processing URL {url}: {e}")
        
        callback_data = CallbackResponseModel(request_id=request_id, data=results)
        send_callback(data=callback_data, callback_url=callback_url)
        print("Background task completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing URLs: {str(e)}")
