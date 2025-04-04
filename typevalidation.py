from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    name: str
    last_name: str
    disabled: bool = False
    password: str

class LoginUser(BaseModel):
    username: str
    password: str
