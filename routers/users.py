from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
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
    return {"message": "User created successfully", "user": new_user.username, "user_id": new_user.id}

@router.post("/login")
def login(user: LoginUser, db: db_dependency):
    db_user = db.query(tables.User).filter(tables.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user": db_user.username , "user_id": db_user.id}

@router.delete("/full_delete/{user_id}")
def full_delete_user(user_id: int, db: db_dependency):
    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. Standortdaten löschen
    db.query(tables.UserLocation).filter(tables.UserLocation.user_id == user_id).delete()

    # 2. Friend Requests löschen (gesendet oder empfangen)
    db.query(tables.FriendRequest).filter(
        (tables.FriendRequest.sender_id == user_id) | 
        (tables.FriendRequest.receiver_id == user_id)
    ).delete()

    # 3. Freundschaften löschen (egal ob user_id sender oder empfänger)
    db.query(tables.UserFriend).filter(
        (tables.UserFriend.user_id == user_id) | 
        (tables.UserFriend.friend_id == user_id)
    ).delete()

    # 4. Besuchte Zonen löschen
    db.query(tables.VisitedZone).filter(tables.VisitedZone.user_id == user_id).delete()

    # 5. Berechnete Polygone löschen
    db.query(tables.VisitedPolygon).filter(tables.VisitedPolygon.user_id == user_id).delete()

    # 6. User löschen
    db.delete(user)
    db.commit()

    return {"message": f"User {user.username} and all related data deleted."}



