from datetime import datetime
from pydantic import BaseModel


# Token
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int | None = None


# Post
class PostBase(BaseModel):
    body: str


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    timestamp: datetime
    owner_id: int
    likes: int
    dislikes: int

    class Config:
        orm_mode = True


# User
class UserBase(BaseModel):
    alias: str


class UserCreate(UserBase):
    password: str
    email: str


class User(UserBase):
    id: int
    # posts: list[Post]

    class Config:
        orm_mode = True


# Reaction
class ReactionBase(BaseModel):
    dislike: bool


class Reaction(ReactionBase):
    pass


class ResponseMessage(BaseModel):
    detail: str
