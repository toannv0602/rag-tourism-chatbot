"""
Request and response models for the API.
"""
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    top_k: int =5

class SourceInfo(BaseModel):
    tour_name: str
    type: str
    url: str
    distance: float

class ChatResponse(BaseModel):
    answer: str
