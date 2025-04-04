from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated
from db import get_db
import models as tables
from typevalidation import UserBase, LoginUser

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
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "disabled": user.disabled
        }
        for user in users
    ]
