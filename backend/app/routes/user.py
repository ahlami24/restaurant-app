from app.schemas.user import UserCreate, UserResponse
from app.models.user import User, UserRole
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.user import create_user as create_user_service
from app.routes.dependencies import require_role
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    duplicate_phone_user = (
        db.query(User).filter(User.phone == user.phone).first()
    )
    if duplicate_phone_user:
        raise HTTPException(
            status_code=400,
            detail="User with this phone number already exists",
        )

    try:
        new_user = create_user_service(
            db,
            user.name,
            user.phone,
            UserRole.customer,
            user.password,
            email=user.email,
        )
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Phone number or email already exists",
        )




@router.get("/", response_model=list[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.platform_admin.value)),
):
    users = db.query(User).all()
    return users