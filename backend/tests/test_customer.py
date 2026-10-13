def test_create_customer(client):
    response = client.post(
        "/customers",
        json={"name": "Test Customer", "phone": "0911000001"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Customer"
    assert response.json()["phone"] == "0911000001"
    assert "id" in response.json()


def test_get_customers(client):
    client.post(
        "/customers",
        json={"name": "Customer One", "phone": "0911000002"},
    )

    response = client.get("/customers")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Customer One"


def test_get_customer_by_id(client):
    created = client.post(
        "/customers",
        json={"name": "Customer Two", "phone": "0911000003"},
    )
    customer_id = created.json()["id"]

    response = client.get(f"/customers/{customer_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Customer Two"


def test_get_missing_customer_returns_404(client):
    response = client.get("/customers/9999")

    assert response.status_code == 404


def test_duplicate_phone_returns_400(client):
    payload = {"name": "First Customer", "phone": "0911000004"}

    first_response = client.post("/customers", json=payload)
    second_response = client.post(
        "/customers",
        json={"name": "Second Customer", "phone": payload["phone"]},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400


def test_update_customer(client):
    created = client.post(
        "/customers",
        json={"name": "Old Name", "phone": "0911000005"},
    )
    customer_id = created.json()["id"]

    response = client.put(
        f"/customers/{customer_id}",
        json={"name": "New Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["phone"] == "0911000005"
