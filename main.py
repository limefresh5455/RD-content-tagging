import os
from typing import List
import concurrent.futures
from fastapi import Depends
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader
from fastapi import FastAPI, UploadFile, File, HTTPException, Query

load_dotenv()

app = FastAPI(title="FastAPI App Endpoints")

API_KEYS = os.getenv('API_KEYS', '').split(',')

# Define an API key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Dependency function to verify the API key
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key in API_KEYS:
        return api_key
    else:
        raise HTTPException(status_code=403,  detail="Invalid or missing API key")

from utils import process_url_with_retry, process_file_with_retry

# ____________________________________________Extract endpoint with multithreading for urls ______________________________________________
@app.post('/extract_urls')
async def extract_urls(urls: str = Query(None), api_key: str = Depends(verify_api_key)):
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

    return results

#__________________________________________endpoint_for_file________________________________________________________
@app.post('/extract_file')
async def extract_file(files: List[UploadFile]=File(None), api_key: str = Depends(verify_api_key) ):
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

    return results
