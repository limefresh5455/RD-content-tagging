import requests
from fastapi import UploadFile
from response_model import CallbackResponseModel
from utils import process_url_with_retry, process_file_with_retry


def send_callback(data : CallbackResponseModel, callback_url):
    try:
        res = requests.post(callback_url, json=data.model_dump(mode='json'))
        print("status code : ", res.status_code)
        res.raise_for_status()        
        # print("data" , res.json())
    except Exception as e:
        print(f"Exception occured: {e}")

def process_files(request_id : str, files : list[UploadFile], callback_url : str):
    print("background task running")
    
    results = [process_file_with_retry(file) for file in files]

    callback_data = CallbackResponseModel(request_id= request_id, data= results)
    send_callback(data = callback_data, callback_url=callback_url)
    print("background task completed")

def process_urls(request_id : str, urls : str, callback_url : str):
    print("background task running")
    urls_list = urls.split(',')
    
    results = [process_url_with_retry(url) for url in urls_list]

    callback_data = CallbackResponseModel(request_id= request_id, data= results)
    send_callback(data=callback_data, callback_url=callback_url)
    print("background task completed")