from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant


def get_restaurants(db: Session) -> list[Restaurant]:
    """Return active restaurants available for public browsing."""
    return (
        db.query(Restaurant)
        .filter(Restaurant.is_active.is_(True))
        .order_by(Restaurant.name)
        .all()
    )


def get_restaurant_by_slug(
    db: Session, restaurant_slug: str
) -> Restaurant | None:
    """Return an active restaurant matching its public slug."""
    return (
        db.query(Restaurant)
        .filter(
            Restaurant.slug == restaurant_slug,
            Restaurant.is_active.is_(True),
        )
        .first()
    )
