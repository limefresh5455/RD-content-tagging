from pydantic import BaseModel, HttpUrl

class TopicSubtopic(BaseModel):
    rank : int = 1
    topic : str 
    subtopic : str 

class ContentModel(BaseModel):
    category_report : list[TopicSubtopic]
    summary : str | None = None

class ResponseModel(BaseModel):
    status : bool
    message : str
    content : ContentModel | list =  []
    url : str | None = None
    filename : str | None = None

class CallbackResponseModel(BaseModel):
    request_id : str
    data : list[ResponseModel]

class QuickCallbackResponseModel(BaseModel):
    request_id : str
    callback_url : HttpUrl
    
