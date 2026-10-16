import getpass
import sys

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth import hash_password


def main():
    print("Create the platform administrator account")
    name = input("Administrator name [Platform Admin]: ").strip()
    name = name or "Platform Admin"

    phone = input("Login phone (required): ").strip()
    if not phone:
        print("A phone number is required.")
        sys.exit(1)

    email = input("Email [leave blank to skip]: ").strip().lower() or None
    password = getpass.getpass("Set administrator password: ")
    confirm = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        print("Use a password with at least 12 characters.")
        sys.exit(1)

    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.phone == phone).first():
            print("That phone number is already registered.")
            sys.exit(1)

        if email and db.query(User).filter(User.email == email).first():
            print("That email address is already registered.")
            sys.exit(1)

        admin = User(
            name=name,
            phone=phone,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.platform_admin,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Platform administrator created successfully. User ID: {admin.id}")
        print("Log in with the phone number and password you entered.")

    except IntegrityError:
        db.rollback()
        print("Could not create account: phone or email may already be in use.")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
