from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
import models as tables
from typevalidation import FriendRequestInput

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/search")
def search_users(db: db_dependency, query: str = Query(..., min_length=1), self_id: int = Query(...)):
    users = db.query(tables.User).filter(
            tables.User.username.ilike(f"%{query}%"),
            tables.User.id != self_id,
            tables.User.disabled == False
            ).all()

    if not users:
        raise HTTPException(status_code=404, detail="No Users found")
    
    result = []

    for user in users:
        # Ausstehende Friend-Request prüfen (self_id → user.id)
        request_sent = db.query(tables.FriendRequest).filter(
            tables.FriendRequest.sender_id == self_id,
            tables.FriendRequest.receiver_id == user.id,
            tables.FriendRequest.status == "pending"
        ).first() is not None

        # Check if user sent self.id a friend request
        request_received = db.query(tables.FriendRequest).filter(
            tables.FriendRequest.sender_id == user.id,
            tables.FriendRequest.receiver_id == self_id,
            tables.FriendRequest.status == "pending"
        ).first() is not None

        # Freundschaft prüfen (egal in welche Richtung)
        already_friends = db.query(tables.UserFriend).filter(
            ((tables.UserFriend.user_id == self_id) & (tables.UserFriend.friend_id == user.id)) |
            ((tables.UserFriend.user_id == user.id) & (tables.UserFriend.friend_id == self_id))
        ).first() is not None

        result.append({
            "id": user.id,
            "username": user.username,
            "disabled": user.disabled,
            "request_sent": request_sent,
            "request_received": request_received,
            "already_friends": already_friends
        })

    return result

@router.post("/send_request")
def send_friend_request(data: FriendRequestInput, db: db_dependency):
    # check if both IDs exist
    sender = db.query(tables.User).filter(tables.User.id == data.sender_id).first()
    receiver = db.query(tables.User).filter(tables.User.id == data.receiver_id).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="One or both users not found")
    if sender.id == receiver.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    # check if a friend request is already pending
    existing = db.query(tables.FriendRequest).filter(
        tables.FriendRequest.sender_id == data.sender_id,
        tables.FriendRequest.receiver_id == data.receiver_id,
        tables.FriendRequest.status == "pending"
    ).first()

    existing_other_way_around = db.query(tables.FriendRequest).filter(
        tables.FriendRequest.sender_id == data.receiver_id,
        tables.FriendRequest.receiver_id == data.sender_id,
        tables.FriendRequest.status == "pending"
    ).first()

    if existing or existing_other_way_around:
        raise HTTPException(status_code=409, detail="Friend request already sent")
    
    # check if already friends
    already_friends = db.query(tables.UserFriend).filter(
        tables.UserFriend.user_id == data.sender_id,
        tables.UserFriend.friend_id == data.receiver_id,
    ).first()
    
    if already_friends:
        raise HTTPException(status_code=409, detail="Already friends")

    # save request
    friend_request = tables.FriendRequest(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id
    )
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)

    return {"message": "Friend request sent", "request_id": friend_request.id}
