from app.models.restaurant import Restaurant


def test_list_restaurants_returns_active_restaurants(client, db_session):
    db_session.add_all([
        Restaurant(name="Baraka Restaurant", slug="baraka-restaurant", is_active=True),
        Restaurant(name="Inactive Restaurant", slug="inactive-restaurant", is_active=False),
    ])
    db_session.commit()

    response = client.get("/restaurants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Baraka Restaurant"
    assert data[0]["slug"] == "baraka-restaurant"


def test_get_restaurant_by_slug(client, db_session):
    db_session.add(
        Restaurant(
            name="Baraka Restaurant",
            slug="baraka-restaurant",
            is_active=True,
        )
    )
    db_session.commit()

    response = client.get("/restaurants/baraka-restaurant")

    assert response.status_code == 200
    assert response.json()["name"] == "Baraka Restaurant"


def test_inactive_restaurant_is_not_publicly_accessible(client, db_session):
    db_session.add(
        Restaurant(
            name="Inactive Restaurant",
            slug="inactive-restaurant",
            is_active=False,
        )
    )
    db_session.commit()

    response = client.get("/restaurants/inactive-restaurant")

    assert response.status_code == 404


def test_unknown_restaurant_returns_404(client):
    response = client.get("/restaurants/unknown-restaurant")

    assert response.status_code == 404
