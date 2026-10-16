from app.models.food import Food


def create_food(db, food, restaurant_id):
    new_food = Food(name=food.name, price=food.price, restaurant_id=restaurant_id)
    db.add(new_food)
    return new_food

def get_foods(db, restaurant_id):
    return db.query(Food).filter(Food.restaurant_id == restaurant_id).all()

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

