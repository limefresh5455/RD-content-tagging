import PyPDF2
from prompt import generate, generate_summary
from langchain.text_splitter import RecursiveCharacterTextSplitter
from response_model import FileResponseModel, FileCategoryModel
from fastapi import UploadFile
#____________________________________Function to handle PDF file categories______________________________________________

def document_categorieser(pdf_file : UploadFile):
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
        return FileCategoryModel(status= True, message = "Documents processed successfully", filename=pdf_file.filename, content=FileResponseModel(**{"category_report": category_report, "summary": all_summary}))
    except Exception as e:
        return FileCategoryModel(status= False, message=f" Error {e}", filename = pdf_file.filename, content = "")