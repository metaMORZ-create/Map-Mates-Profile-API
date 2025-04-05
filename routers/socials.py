from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
import models as tables
from typevalidation import FriendRequestInput, AcceptRequestInput

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

@router.post("/accept_request")
def accept_friend_request(data: AcceptRequestInput, db: db_dependency):
    friend_request = db.query(tables.FriendRequest).filter(
        tables.FriendRequest.sender_id == data.sender_user_id,
        tables.FriendRequest.receiver_id == data.self_user_id,
        tables.FriendRequest.status == "pending"
    ).first()

    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found or already handled")
    
    if friend_request.receiver_id != data.self_user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to accept this friend request")
    
    # Add friendship both ways around
    db.add_all([
        tables.UserFriend(user_id=data.self_user_id, friend_id=data.sender_user_id),
        tables.UserFriend(user_id=data.sender_user_id, friend_id=data.self_user_id)
    ])

    friend_request.status = "accepted"

    db.commit()

    return {"message": "Friend request accepted"}

@router.post("/deny_request")
def deny_friend_request(data: AcceptRequestInput, db: db_dependency):
    friend_request = db.query(tables.FriendRequest).filter(
        tables.FriendRequest.status == "pending",
        (
            (tables.FriendRequest.sender_id == data.sender_user_id) &
            (tables.FriendRequest.receiver_id == data.self_user_id)
        ) |
        (
            (tables.FriendRequest.sender_id == data.self_user_id) &
            (tables.FriendRequest.receiver_id == data.sender_user_id)
        )
    ).first()

    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found or already handled")
    
    if data.self_user_id not in [friend_request.sender_id, friend_request.receiver_id]:
        raise HTTPException(status_code=403, detail="You are not authorized to deny this friend request")
    
    # Add friendship both ways around

    db.delete(friend_request)

    db.commit()

    return {"message": "Friend request denied"}

@router.get("/outgoing_requests/{self_id}")
def get_outgoing_request(self_id: int, db: db_dependency):
    requests = (
        db.query(
            tables.FriendRequest,
            tables.User.username.label("receiver_username")
        )
        .join(tables.User, tables.FriendRequest.receiver_id == tables.User.id)
        .filter(
            tables.FriendRequest.sender_id == self_id,
            tables.FriendRequest.status == "pending"
        )
        .all()
    )

    return [
        {
            "request_id": req.FriendRequest.id,
            "receiver_id": req.FriendRequest.receiver_id,
            "receiver_username": req.receiver_username,
            "status": req.FriendRequest.status,
            "created_at": req.FriendRequest.created_at
        }
        for req in requests
    ]

@router.get("/received_requests/{self_id}")
def get_received_request(self_id: int, db: db_dependency):
    requests = (
        db.query(
            tables.FriendRequest,
            tables.User.username.label("sender_username")
        )
        .join(tables.User, tables.FriendRequest.sender_id == tables.User.id)
        .filter(
            tables.FriendRequest.receiver_id == self_id,
            tables.FriendRequest.status == "pending"
        )
        .all()
    )

    return [
        {
            "request_id": req.FriendRequest.id,
            "sender_id": req.FriendRequest.sender_id,
            "sender_username": req.sender_username,
            "status": req.FriendRequest.status,
            "created_at": req.FriendRequest.created_at
        }
        for req in requests
    ]

@router.get("/get_friends/{self_id}")
def get_friends(self_id: int, db: db_dependency):
    friends = (
        db.query(
            tables.UserFriend,
            tables.User.username.label("friend_username")
        )
        .join(tables.User, tables.UserFriend.friend_id == tables.User.id)
        .filter(tables.UserFriend.user_id == self_id)
        .all()
    )

    return [
        {
            "friend_id": friend.UserFriend.friend_id,
            "friend_username": friend.friend_username,
            "friendship_id": friend.UserFriend.id
        }
        for friend in friends
    ]

