import os
import uuid
from typing import List
from fastapi import Depends
from typing import Annotated
from tasks import process_files, process_urls
from fastapi.security.api_key import APIKeyHeader
from utils import process_url_with_retry, process_file_with_retry
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from response_model import QuickCallbackResponseModel, ResponseModel

app = FastAPI(title="FastAPI App Endpoints")

API_KEYS = os.getenv('API_KEYS', '').split(',')
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Dependency function to verify the API key
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key in API_KEYS:
        return api_key
    else:
        raise HTTPException(status_code=403,  detail="Invalid or missing API key")

# ____________________________________________Extract endpoint with multithreading for urls ______________________________________________


@app.post('/extract_urls', response_model= list[ResponseModel])
async def extract_urls(urls: Annotated[str, Query()], api_key: str = Depends(verify_api_key)):
    urls_list = urls.split(',')
    
    results = [process_url_with_retry(url) for url in urls_list]    
    return results


@app.post('/extract_urls_callback', response_model= QuickCallbackResponseModel , responses={
    200 : {
        'description' : "Files are being processed",
        "content" : {
            "application/json" : {
                "example" : {
                    "request_id": "e524ea8c-0e9c-460f-a756-83f045d3f43a",
                    "callback_url": "http://callback_url/endpoint"
                }
            }
        }
    }
}, tags= ["Callback"])

async def extract_urls(background_tasks : BackgroundTasks, urls: Annotated[str, Query()], callback_url : Annotated[str, Query()], api_key: str = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())
    background_tasks.add_task(process_urls, request_id, urls, callback_url)
    return {"request_id": request_id, "callback_url": callback_url}


#__________________________________________endpoint_for_file________________________________________________________
@app.post('/extract_file', response_model= list[ResponseModel])
async def extract_file(files: List[UploadFile] = File(), api_key: str = Depends(verify_api_key)):    

    results = [process_file_with_retry(file) for file in files]

    return results

@app.post('/extract_file_callback', response_model= QuickCallbackResponseModel , responses={
    200 : {
        'description' : "Files are being processed",
        "content" : {
            "application/json" : {
                "example" : {
                    "request_id": "e524ea8c-0e9c-460f-a756-83f045d3f43a",
                    "callback_url": "http://callback_url/endpoint"
                }
            }
        }
    }
}, tags= ["Callback"])
async def extract_file(background_tasks : BackgroundTasks, files: List[UploadFile]=File(), api_key: str = Depends(verify_api_key), callback_url: str = Query()):
    request_id = str(uuid.uuid4())
    background_tasks.add_task(process_files, request_id, files, callback_url)

    return {"request_id": request_id, "callback_url": callback_url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)