from datetime import datetime

from sqlalchemy.orm import Session

from . import models, schemas, security


class NoPermission(Exception):
    pass


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_alias(db: Session, alias: str) -> models.User | None:
    return db.query(models.User).filter(models.User.alias == alias).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.hash_password(user.password)
    db_user = models.User(
        email=user.email,
        alias=user.alias,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_posts(db: Session, skip: int = 0, limit: int = 100, user_id: int | None = None):
    if user_id is not None:
        return db.query(models.Post).filter(models.Post.owner_id == user_id).offset(skip).limit(limit).all()
    return db.query(models.Post).offset(skip).limit(limit).all()


def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_user_posts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Post).filter(models.Post.owner_id == user_id).offset(skip).limit(limit).all()


def create_user_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(
        body=post.body,
        owner_id=user_id,
        timestamp=datetime.now()
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def edit_user_post(db: Session, post_id: int, post: schemas.PostBase, user_id: int):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        return None
    if db_post.owner_id != user_id:
        raise NoPermission()
    db_post.body = post.body
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_user_post(db: Session, post_id: int, user_id: int):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        return False
    if db_post.owner_id != user_id:
        raise NoPermission()
    db.delete(db_post)
    db.commit()
    return True


# Reactions
def react_user_post(db: Session, post_id: int, user_id: int, dislike: bool = False):
    db_post = get_post(db, post_id)
    if db_post.owner_id == user_id:
        raise NoPermission()
    reaction = db.query(models.PostReaction)\
        .filter(models.PostReaction.post_id == post_id)\
        .filter(models.PostReaction.user_id == user_id).first()
    if reaction:
        reaction.dislike = dislike
    else:
        reaction = models.PostReaction(
            post_id=post_id,
            user_id=user_id,
            dislike=dislike
        )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def delete_reaction_user_post(db: Session, post_id: int, user_id: int):
    reaction = db.query(models.PostReaction)\
        .filter(models.PostReaction.post_id == post_id)\
        .filter(models.PostReaction.user_id == user_id).first()
    if reaction:
        db.delete(reaction)
        db.commit()
        db.refresh(reaction)
    return reaction.post


def get_posts_reactions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100, dislike: bool = False):
    posts = db.query(models.Post).join(models.PostReaction).filter(models.PostReaction.user_id == user_id)\
        .filter(models.PostReaction.dislike == dislike).offset(skip).limit(limit).all()
    return posts


def get_users_reactions_by_post(db: Session, post_id: int, skip: int = 0, limit: int = 100, dislike: bool = False):
    users = db.query(models.User).join(models.PostReaction).filter(models.PostReaction.post_id == post_id)\
        .filter(models.PostReaction.dislike == dislike).offset(skip).limit(limit).all()
    return users

