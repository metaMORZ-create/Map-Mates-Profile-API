from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from .. db import get_db
from hashing import hash_password, verify_password
import models as tables
from typevalidation import UserBase, LoginUser

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/register")
def create_user(user: UserBase, db: db_dependency):
    existing_user = db.query(tables.User).filter(tables.User.username == user.username).first()
    existing_email = db.query(tables.User).filter(tables.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = tables.User(username=user.username, email=user.email, disabled=user.disabled, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": new_user.username}

@router.post("/login")
def login(user: LoginUser, db: db_dependency):
    db_user = db.query(tables.User).filter(tables.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user": db_user.username}

@router.delete("/delete/{username}")
def delete_user(username: str, db: db_dependency):
    user = db.query(tables.User).filter(tables.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User '{username}' deleted"}
