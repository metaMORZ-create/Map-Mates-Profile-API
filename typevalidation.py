from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    disabled: bool = False
    password: str

class LoginUser(BaseModel):
    username: str
    password: str
