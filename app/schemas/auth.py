from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    user_id: Optional[int] = None
    
class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str
    
class GoogleUser(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None 