from pydantic import BaseModel, HttpUrl

class FileResponseModel(BaseModel):
    category_report : str
    summary : str

class BaseCategoryModel(BaseModel):
    status : bool
    message : str
    content : str | FileResponseModel

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
    
