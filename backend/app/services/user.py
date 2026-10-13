from app.models.user import User
from app.services.auth import hash_password
from app.models.customer import Customer
from sqlalchemy import or_

def create_user(db, name, phone, role, password, email=None):
    if email:
        email = email.strip().lower()
    new_user = User(
        name=name,
        phone=phone,
        role=role,
        password_hash=hash_password(password),
        email=email

    )

    db.add(new_user)
    db.flush()

    if role == 'customer':
        new_customer = Customer(name=name, phone=phone, user_id=new_user.id)
        db.add(new_customer)
    return new_user

def get_user_by_login(db, identifier: str):
    identifier = identifier.strip()
    return db.query(User).filter(
        or_(
            User.email == identifier.lower(),
            User.phone == identifier
        )
    ).first()