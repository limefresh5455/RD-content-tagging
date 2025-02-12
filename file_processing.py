import PyPDF2
import requests
from io import BytesIO
from fastapi import UploadFile,HTTPException
from prompt import generate, generate_summary
from langchain.text_splitter import RecursiveCharacterTextSplitter
from starlette.datastructures import UploadFile as StarletteUploadFile
from response_model import ResponseModel, ContentModel

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
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        if from_url:
            raise HTTPException(status_code=500, detail=f"Error processing file from URL: {str(e)}")
        # return ResponseModel(status= False, message=f" Error {e}", filename = pdf_file.filename)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def process_file_source_url(source_url : str) -> UploadFile:
    """
    Downloads the pdf file using the public URL from azure storage, return the file content as UploadFile
    """
    print("Downlaoding file")
    try:
        response = requests.get(source_url)
        response.raise_for_status()
        if response.status_code == 200:
            print("File download successfully")
            pdf_file = BytesIO(response.content)

            upload_file = StarletteUploadFile(file = pdf_file, filename="download_file.pdf")
            return document_categorieser(upload_file, from_url= source_url)
    except Exception as e:
        # return ResponseModel(status= False, message=f" Error {e}", url = source_url)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
