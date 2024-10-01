from pydantic import BaseModel, HttpUrl

class TopicSubtopic(BaseModel):
    rank : int = 1
    topic : str 
    subtopic : str 

class FileResponseModel(BaseModel):
    category_report : list[TopicSubtopic]
    summary : str

class BaseCategoryModel(BaseModel):
    status : bool
    message : str
    content : list[TopicSubtopic] | FileResponseModel | dict

class URLCategoryModel(BaseCategoryModel):
    url: str

class FileCategoryModel(BaseCategoryModel):
    filename : str

class CallbackResponseModel(BaseModel):
    request_id : str
    data : list[URLCategoryModel | FileCategoryModel]

class QuickCallbackResponseModel(BaseModel):
    request_id : str
    callback_url : HttpUrl
    
