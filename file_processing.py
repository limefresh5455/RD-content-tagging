import json
import time
import PyPDF2
import requests
import traceback
from io import BytesIO
from openai import OpenAIError
from fastapi import UploadFile,HTTPException
from response_model import ResponseModel, ContentModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from starlette.datastructures import UploadFile as StarletteUploadFile
from prompt import generate, generate_summary, topic_subtopic_pairs_str, system_instructions

#____________________________________Function to handle PDF file categories______________________________________________

def document_categorieser(pdf_file : UploadFile, from_url : str = None):
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
        # return {"category_report": category_report, "summary": all_summary}
        if from_url:
            return ResponseModel(status= True, message = "Documents processed successfully", url= from_url, content=ContentModel(**{"category_report": category_report, "summary": all_summary}))        
        return ResponseModel(status= True, message = "Documents processed successfully", filename=pdf_file.filename, content=ContentModel(**{"category_report": category_report, "summary": all_summary}))
    
    except OpenAIError as e:        
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    except Exception as e:        
        print(traceback.format_exc())
        if from_url:
            raise HTTPException(status_code=500, detail=f"Error processing file from URL: {str(e)}")
        # return ResponseModel(status= False, message=f" Error {e}", filename = pdf_file.filename)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

from google import genai
from pydantic import BaseModel

client = genai.Client()

class CategoryReport(BaseModel):
    topic: str
    subtopic: str
    summary: str

def file_processor_gemini(pdf_file : UploadFile, mime_type: str, from_url : str = None):
    try:        
        gemini_file = client.files.upload(file=pdf_file.file, config = {"mime_type": mime_type})
        
        if mime_type == "video/mp4":
        # Check whether the file is ready to be used.
            while gemini_file.state.name == "PROCESSING":
                print('.', end='')
                time.sleep(1)
                gemini_file = client.files.get(name=gemini_file.name)

            if gemini_file.state.name == "FAILED":
                raise ValueError(gemini_file.state.name)

        print('Done')
        response = client.models.generate_content(
            model = 'gemini-1.5-flash',
            contents = [gemini_file, system_instructions],
            config={
                'response_mime_type': 'application/json',
                'response_schema': CategoryReport
            }
        )
        # print(response.text)
        response_json = json.loads(response.text)
        client.files.delete(name=gemini_file.name)
        if from_url:
            return ResponseModel(status= True, message = "Documents processed successfully", url= from_url, content=ContentModel(**{"category_report": [{"topic" : response_json['topic'], "subtopic" : response_json['subtopic']}], "summary": response_json['summary']}))
        return ResponseModel(status= True, message = "Documents processed successfully", filename=pdf_file.filename, content=ContentModel(**{"category_report": [{"topic" : response_json['topic'], "subtopic" : response_json['subtopic']}], "summary": response_json['summary']}))
    except Exception as e:
        print(traceback.format_exc())
        if gemini_file:            
            client.files.delete(name=gemini_file.name)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
def process_file_source_url(source_url : str, mime_type: str) -> UploadFile:
    """
    Downloads the pdf file using the public URL from azure storage, return the file content as UploadFile
    """
    print("Downloding file")
    try:
        response = requests.get(source_url)
        response.raise_for_status()
        if response.status_code == 200:
            print("File downloaded successfully")
            pdf_file = BytesIO(response.content)

            upload_file = StarletteUploadFile(file = pdf_file, filename="download_file.pdf")
            # return document_categorieser(upload_file, from_url= source_url)
            return file_processor_gemini(upload_file, mime_type= mime_type, from_url= source_url)
    except Exception as e:
        # return ResponseModel(status= False, message=f" Error {e}", url = source_url)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

from google.genai import types
def process_youtube_url(url):
    response = client.models.generate_content(
    model='models/gemini-2.0-flash',
    contents=types.Content(
        parts=[
            types.Part(text=system_instructions),
            types.Part(
                file_data=types.FileData(file_uri=url)
            )
        ]
    ),
    config={
            'response_mime_type': 'application/json',
            'response_schema': CategoryReport
            }
    )
    response_json = json.loads(response.text)
    return ResponseModel(status= True, message = "Documents processed successfully", url= url, content=ContentModel(**{"category_report": [{"topic" : response_json['topic'], "subtopic" : response_json['subtopic']}], "summary": response_json['summary']}))