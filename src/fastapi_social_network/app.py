import re
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


SECRET_KEY = f"{'_not_a_secret_':x^64}"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SUB_RE = re.compile(r"^user:id:(\d*)$")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_alias(db=db, alias=username)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User | None:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        u_id = SUB_RE.findall(sub)
        if len(u_id) == 0:
            raise credentials_exception
        token_data = schemas.TokenData(id=u_id[0])
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db=db, user_id=token_data.id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)) -> models.User | None:
    return current_user


@app.post("/token", response_model=schemas.Token)
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


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = crud.get_user_by_alias(db, alias=user.alias)
    if db_user:
        raise HTTPException(status_code=400, detail="Alias already in use")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/me", response_model=schemas.User)
def read_user_self(user: models.User = Depends(get_current_active_user)):
    return user


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_id}/posts", response_model=list[schemas.Post])
def read_user_posts(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, skip=skip, limit=limit, user_id=user_id)


@app.get("/posts/", response_model=list[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, skip=skip, limit=limit)


@app.post("/posts/", response_model=schemas.Post)
def create_post(post: schemas.PostCreate, user: models.User = Depends(get_current_active_user),
                db: Session = Depends(get_db)):
    return crud.create_user_post(db=db, post=post, user_id=user.id)


@app.get("/posts/{post_id}", response_model=schemas.Post)
def get_post(post_id: int, db: Session = Depends(get_db)):
    return crud.get_post(db=db, post_id=post_id)


@app.put("/posts/{post_id}", response_model=schemas.Post)
def update_post(post_id: int, post: schemas.PostBase, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_active_user)):
    try:
        edited_post = crud.edit_user_post(db=db, post_id=post_id, post=post, user_id=user.id)
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action not allowed"
        )
    else:
        if not edited_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No such post"
            )
        return edited_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
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
                detail="No such post"
            )


# Reactions
@app.put("/posts/{post_id}/clear_like", response_model=schemas.Post)
def clear_like_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    return crud.delete_reaction_user_post(db=db, post_id=post_id, user_id=user.id)


# Like
@app.get("/posts/{post_id}/likes/", response_model=list[schemas.User])
def get_post_likes(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users_reactions_by_post(db=db, post_id=post_id, skip=skip, limit=limit, dislike=False)


@app.get("/users/{user_id}/likes/", response_model=list[schemas.Post])
def get_user_likes(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts_reactions_by_user(db=db, user_id=user_id, skip=skip, limit=limit, dislike=False)


@app.put("/posts/{post_id}/like", response_model=schemas.Post)
def like_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    try:
        reaction = crud.react_user_post(db=db, post_id=post_id, user_id=user.id, dislike=False)
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot like own post"
        )
    else:
        return reaction.post


# Dislike
@app.get("/posts/{post_id}/dislikes/", response_model=list[schemas.User])
def get_post_dislikes(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users_reactions_by_post(db=db, post_id=post_id, skip=skip, limit=limit, dislike=True)


@app.get("/users/{user_id}/dislikes/", response_model=list[schemas.Post])
def get_user_dislikes(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts_reactions_by_user(db=db, user_id=user_id, skip=skip, limit=limit, dislike=True)


@app.put("/posts/{post_id}/dislike", response_model=schemas.Post)
def dislike_post(post_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_active_user)):
    try:
        reaction = crud.react_user_post(db=db, post_id=post_id, user_id=user.id, dislike=True)
    except crud.NoPermission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot dislike own post"
        )
    else:
        return reaction.post
