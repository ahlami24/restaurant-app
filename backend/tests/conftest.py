import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import (
    customer,  # noqa: F401
    delivery_person,  # noqa: F401
    food,  # noqa: F401
    order,  # noqa: F401
    order_item,  # noqa: F401
    restaurant,  # noqa: F401
)
from app.models import (
    user as user_model,  # noqa: F401
)
from app.models.base import Base
from app.models.user import User, UserRole
from app.services.auth import create_access_token, hash_password


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def make_user(db_session):
    def _make_user(
        *,
        name="Test User",
        phone,
        email=None,
        role=UserRole.user,
    ):
        new_user = User(
            name=name,
            phone=phone,
            email=email,
            password_hash=hash_password("TestPassword123"),
            role=role,
        )
        db_session.add(new_user)
        db_session.flush()
        return new_user

    return _make_user


@pytest.fixture
def auth_headers():
    def _auth_headers(user):
        token = create_access_token(user.id, user.role.value)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers