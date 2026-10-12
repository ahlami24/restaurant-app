from app.models.user import User
from app.services.auth import hash_password
from app.models.customer import Customer

def create_user(db, name, phone, role, password):
    new_user = User(
        name=name,
        phone=phone,
        role=role,
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.flush()

    if role == 'customer':
        new_customer = Customer(name=name, phone=phone, user_id=new_user.id)
        db.add(new_customer)
        
    return new_user

