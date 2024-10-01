import requests
from prompt import generate
from bs4 import BeautifulSoup
from response_model import URLCategoryModel, TopicSubtopic
from langchain.text_splitter import RecursiveCharacterTextSplitter

# _______________________Fetch HTML content from the URL and extract text___________________________________________

def fetch_and_extract_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        return text_content
    except requests.RequestException as e:
        return None
    
#___________________________ Function to handle URL categories___________________________________________________________

def categories_url(url):
    text_content = fetch_and_extract_text(url)
    if not text_content:
        return URLCategoryModel(status=False, message = "Failed to fetch or extract text from the URL", url=url,content={})
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=1000)
    chunks = text_splitter.create_documents([text_content])
    # print("chunks", chunks)
    categories = generate(chunks[0].page_content)
    # return categories
    return URLCategoryModel(status=True, message = "Categories extracted successfully", url=url, content=categories)

