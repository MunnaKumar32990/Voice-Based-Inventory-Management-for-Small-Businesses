from pydantic import BaseModel

class DemoLoginRequest(BaseModel):
    shop_name: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
