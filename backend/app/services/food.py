from app.models.food import Food


def create_food(db, food, restaurant_id):
    new_food = Food(name=food.name, price=food.price, category=food.category, restaurant_id=restaurant_id)
    db.add(new_food)
    return new_food

def get_foods(db, restaurant_id, search=None, min_price=None, max_price=None, category=None, sort_by=None):
    query = db.query(Food).filter(Food.restaurant_id == restaurant_id)
    if search:
        query = query.filter(Food.name.ilike(f"%{search}%"))
    if min_price is not None:
        query = query.filter(Food.price >= min_price)
    if max_price is not None:
        query = query.filter(Food.price <= max_price)
    if category is not None:
        query = query.filter(Food.category.ilike(category))
    if sort_by is not None:
        if sort_by == "price_asc":
            query = query.order_by(Food.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Food.price.desc())
        else:
            query = query.order_by(Food.name.asc())
    else:
        query = query.order_by(Food.name.asc())
    return query.all()

def get_food(db, food_id, restaurant_id):
    return db.query(Food).filter(Food.id == food_id, Food.restaurant_id == restaurant_id).first()

def update_food(db, food_id, food, restaurant_id):
    existing_food = db.query(Food).filter(Food.id == food_id, Food.restaurant_id == restaurant_id).first()
    if existing_food is None:
        return None

    update_data = food.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_food, key, value)

    return existing_food
def delete_food(db, food_id, restaurant_id):
    food = db.query(Food).filter(Food.id == food_id, Food.restaurant_id == restaurant_id).first()
    if food is None:
        return None

    db.delete(food)
    return True

