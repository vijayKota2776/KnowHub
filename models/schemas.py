from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600

class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    reputation: float
    created_at: float
    following_count: int
    followers_count: int
    followed_topics: List[str]

class QuestionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=256)
    content: str = Field(..., min_length=10)
    topic_ids: List[str] = []

class QuestionResponse(BaseModel):
    question_id: str
    author_id: str
    author_username: Optional[str] = None
    title: str
    content: str
    topic_ids: List[str]
    created_at: float

class AnswerCreate(BaseModel):
    content: str = Field(..., min_length=5)

class AnswerResponse(BaseModel):
    answer_id: str
    question_id: str
    author_id: str
    author_username: Optional[str] = None
    content: str
    upvotes: int
    downvotes: int
    created_at: float
    ranking_score: Optional[float] = None
    author_reputation: Optional[float] = None

class VoteRequest(BaseModel):
    vote_type: str = Field(..., pattern="^(upvote|downvote)$")

class VoteResponse(BaseModel):
    answer_id: str
    upvotes: int
    downvotes: int

class TopicCreate(BaseModel):
    topic_id: str
    name: str
    description: str

class TopicResponse(BaseModel):
    topic_id: str
    name: str
    description: str
    created_at: float

class FeedResponse(BaseModel):
    data: List[QuestionResponse]
    next_page_token: Optional[str] = None

class SearchResult(BaseModel):
    question_id: str
    title: str
    content: str
    author_id: str
    author_username: Optional[str] = None
    created_at: float
    search_score: float
    lexical_score: float
    semantic_score: float
