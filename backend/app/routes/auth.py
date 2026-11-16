from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.user import LoginRequest, UserResponse
from app.services.auth import create_access_token, verify_password
from app.services.user import get_user_by_login

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    login_request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_login(db, login_request.identifier)

    if not user or not verify_password(
        login_request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    access_token = create_access_token(user.id, user.role.value)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user