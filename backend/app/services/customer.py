from app.models.customer import Customer


def get_customers(db):
    return db.query(Customer).all()


def get_customer_by_id(db, customer_id):
    return db.query(Customer).filter(Customer.id == customer_id).first()


def update_customer(db, customer_id, customer_update):
    """Update profile fields stored on the linked User.

    The phone field is also the account's phone-based login identifier.
    """
    customer = get_customer_by_id(db, customer_id)
    if customer is None:
        return None

    if customer_update.name is not None:
        customer.user.name = customer_update.name
    if customer_update.phone is not None:
        customer.user.phone = customer_update.phone

    return customer


def delete_customer(db, customer_id):
    customer = get_customer_by_id(db, customer_id)
    if customer is None:
        return None
    db.delete(customer)
    return customer
