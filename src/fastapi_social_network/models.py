from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    alias = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    posts = relationship("Post", back_populates="owner")
    reactions = relationship("PostReaction", back_populates="user", cascade="all, delete, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    body = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="posts")
    reactions = relationship("PostReaction", back_populates="post", cascade="all, delete, delete-orphan")


class PostReaction(Base):
    __tablename__ = "post_reaction"
    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    dislike = Column(Boolean, default=False)
    user = relationship("User", back_populates="reactions")
    post = relationship("Post", back_populates="reactions")

