from getpass import getpass

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth import hash_password


def create_owner():
    db = SessionLocal()

    try:
        name = input("Restaurant owner's name: ").strip()
        phone = input("Restaurant owner's phone: ").strip()
        password = getpass("Password: ")
        confirm_password = getpass("Confirm password: ")

        if not name or not phone or not password:
            print("Name, phone, and password are required.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        existing_user = (
            db.query(User)
            .filter(User.phone == phone)
            .first()
        )

        if existing_user:
            print("A user with this phone number already exists.")
            return

        owner = User(
            name=name,
            phone=phone,
            password_hash=hash_password(password),
            role=UserRole.restaurant_owner,
        )

        db.add(owner)
        db.commit()

        print("Restaurant owner created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_owner()