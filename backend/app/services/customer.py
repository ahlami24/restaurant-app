from app.models.customer import Customer

def get_customers(db):
    return db.query(Customer).all()

def get_customer_by_id(db, customer_id):
    return db.query(Customer).filter(Customer.id == customer_id).first()

def update_customer(db, customer_id, customer_update):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return None

    if customer_update.name is not None:
        customer.name = customer_update.name
    if customer_update.phone is not None:
        customer.phone = customer_update.phone

    return customer

def delete_customer(db, customer_id):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return None
    db.delete(customer)
    return customer