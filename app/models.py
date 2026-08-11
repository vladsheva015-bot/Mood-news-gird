from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NewsItem(BaseModel):
    title: str
    content: str
    source: str
    url: str
    published_at: datetime


class NewsDB(BaseModel):
    id: int
    title: str
    content: str
    source: str
    url: str
    published_at: str
    original_json: str


class RewrittenNews(BaseModel):
    id: int
    news_id: int
    mood: str
    rewritten_content: str
    created_at: datetime