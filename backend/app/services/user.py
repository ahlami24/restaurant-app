from sqlalchemy import or_

from app.models.user import User, UserRole
from app.services.auth import hash_password


def create_user(db, name, phone, role, password, email=None):
    if email:
        email = email.strip().lower()

    new_user = User(
        name=name,
        phone=phone,
        role=role,
        password_hash=hash_password(password),
        email=email,
    )

    db.add(new_user)
    db.flush()

    return new_user


def get_user_by_login(db, identifier: str):
    identifier = identifier.strip()

    return (
        db.query(User)
        .filter(
            or_(
                User.email == identifier.lower(),
                User.phone == identifier,
            )
        )
        .first()
    )
