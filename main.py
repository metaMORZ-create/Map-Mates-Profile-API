from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import models as models
from db import SessionLocal, engine
from typevalidation import UserBase
from hashing import hash_password
from sqlalchemy.orm import Session
from typing import List, Annotated

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

print("Für Git")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/register")
def create_user(user: UserBase, db: db_dependency):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = models.User(username=user.username, email=user.email, name=user.name, last_name=user.last_name, disabled=user.disabled, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": new_user.username}

app.post("/login")
def login(user: UserBase, db: db_dependency):
    hashed_password = hash_password(user.password)
    db_user = db.query(models.User).filter(models.User.username == user.username, models.User.hashed_password == hashed_password).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user": db_user.username}

