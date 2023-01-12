import re
from datetime import timedelta

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..config import settings
from ..database import engine
from ..dependencies import authenticate_user, get_current_active_user, create_access_token, get_db

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SUB_RE = re.compile(r"^user:id:(\d*)$")

RESPONSE_401 = {"model": schemas.ResponseMessage, "description": "Not authenticated"}
RESPONSE_403 = {"model": schemas.ResponseMessage, "description": "No permission"}
RESPONSE_404 = {"model": schemas.ResponseMessage, "description": "Item not found"}

router = APIRouter(
    responses={
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404
    }
)


@router.post("/token", response_model=schemas.Token, responses={401: RESPONSE_401})
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": f"user:id:{user.id}"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = crud.get_user_by_alias(db, alias=user.alias)
    if db_user:
        raise HTTPException(status_code=400, detail="Alias already in use")
    return crud.create_user(db=db, user=user)


@router.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/me", response_model=schemas.User, responses={401: RESPONSE_401})
def read_user_self(user: models.User = Depends(get_current_active_user)):
    return user


@router.get("/users/{user_id}", response_model=schemas.User, responses={404: RESPONSE_404})
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/users/{user_id}/posts", response_model=list[schemas.Post], responses={404: RESPONSE_404})
def read_user_posts(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_posts = crud.get_posts(db=db, skip=skip, limit=limit, user_id=user_id)
    if db_posts is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_posts


@router.get("/posts/", response_model=list[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, skip=skip, limit=limit)


@router.post("/posts/", response_model=schemas.Post)
def create_post(post: schemas.PostCreate, user: models.User = Depends(get_current_active_user),
                db: Session = Depends(get_db)):
    return crud.create_user_post(db=db, post=post, user_id=user.id)


@router.get("/posts/{post_id}", response_model=schemas.Post, responses={404: RESPONSE_404})
def get_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post(db=db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.put("/posts/{post_id}", response_model=schemas.Post, responses={404: RESPONSE_404, 403: RESPONSE_403})
def update_post(post_id: int, post: schemas.PostBase, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_active_user)):
    try:
        edited_db_post = crud.edit_user_post(db=db, post_id=post_id, post=post, user_id=user.id)
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action not allowed"
        )
    else:
        if not edited_db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return edited_db_post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: RESPONSE_404, 403: RESPONSE_403})
def delete_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    try:
        result = crud.delete_user_post(db=db, post_id=post_id, user_id=user.id)
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action not allowed"
        )
    else:
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )


# Reactions
@router.delete("/posts/{post_id}/likes/", response_model=schemas.Post, responses={404: {"model": str}})
@router.delete("/posts/{post_id}/dislikes/", response_model=schemas.Post, responses={404: RESPONSE_404})
@router.delete("/posts/{post_id}/clear_reaction/", response_model=schemas.Post, responses={404: RESPONSE_404})
def clear_reaction_post(post_id: int, db: Session = Depends(get_db),
                        user: models.User = Depends(get_current_active_user)):
    """
    Clears the reaction (like, dislike) off a Post, provided Post id.
    Alternative paths provided for convenience; be wary that it will remove both like or dislike!
    """
    db_post = crud.delete_reaction_user_post(db=db, post_id=post_id, user_id=user.id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


# Like
@router.get("/posts/{post_id}/likes/", response_model=list[schemas.User], responses={404: RESPONSE_404})
def get_post_likes(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_users = crud.get_users_reactions_by_post(db=db, post_id=post_id, skip=skip, limit=limit, dislike=False)
    if db_users is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_users


@router.get("/users/me/likes/", response_model=list[schemas.Post])
def get_user_self_likes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        user: models.User = Depends(get_current_active_user)):
    db_posts = crud.get_posts_reactions_by_user(db=db, user_id=user.id, skip=skip, limit=limit, dislike=False)
    return db_posts


@router.get("/users/{user_id}/likes/", response_model=list[schemas.Post], responses={404: RESPONSE_404})
def get_user_likes(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_posts = crud.get_posts_reactions_by_user(db=db, user_id=user_id, skip=skip, limit=limit, dislike=False)
    if db_posts is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_posts


@router.put("/posts/{post_id}/likes/", response_model=schemas.Post, responses={404: RESPONSE_404, 403: RESPONSE_403})
def like_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    try:
        db_post = crud.react_user_post(db=db, post_id=post_id, user_id=user.id, dislike=False)
        if db_post is None:
            raise HTTPException(status_code=404, detail="Post not found")
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot like own post"
        )
    else:
        return db_post


# Dislike
@router.get("/posts/{post_id}/dislikes/", response_model=list[schemas.User], responses={404: RESPONSE_404})
def get_post_dislikes(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_users = crud.get_users_reactions_by_post(db=db, post_id=post_id, skip=skip, limit=limit, dislike=True)
    if db_users is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_users


@router.get("/users/me/dislikes/", response_model=list[schemas.Post])
def get_user_self_dislikes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                           user: models.User = Depends(get_current_active_user)):
    db_posts = crud.get_posts_reactions_by_user(db=db, user_id=user.id, skip=skip, limit=limit, dislike=True)
    return db_posts


@router.get("/users/{user_id}/dislikes/", response_model=list[schemas.Post], responses={404: RESPONSE_404})
def get_user_dislikes(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_posts = crud.get_posts_reactions_by_user(db=db, user_id=user_id, skip=skip, limit=limit, dislike=True)
    if db_posts is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_posts


@router.put("/posts/{post_id}/dislikes/", response_model=schemas.Post, responses={404: RESPONSE_404, 403: RESPONSE_403})
def dislike_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    try:
        db_post = crud.react_user_post(db=db, post_id=post_id, user_id=user.id, dislike=True)
        if db_post is None:
            raise HTTPException(status_code=404, detail="Post not found")
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot dislike own post"
        )
    else:
        return db_post
