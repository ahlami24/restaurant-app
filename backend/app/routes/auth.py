from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import LoginRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.services.auth import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    access_token = create_access_token(user.id, user.role.value)
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user