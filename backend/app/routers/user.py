from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import db
from app.db import models
from app import schema as schemas
from app.core import auth

router = APIRouter(
    prefix="/users",
    tags = ["users"]
)

@router.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, session: Session = Depends(db.get_db)):
    
    db_user = session.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hash_pwd = auth.get_password_hash(user.password)

    new_user = models.User(
        email=user.email,
        hashed_password=hash_pwd
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.post("/login")
def login(user_credentials: schemas.UserCreate, session: Session = Depends(db.get_db)):
    user = session.query(models.User).filter(models.User.email == user_credentials.email).first()

    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    access_token = auth.create_access_token(data={"sub" : user.email})
    return {"access_token": access_token, "token_type": "bearer"}
        