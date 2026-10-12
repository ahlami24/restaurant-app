from fastapi import FastAPI
from app.routes.user import router as user_router
from app.routes.food import router as food_router
from app.routes.order import router as order_router
from app.routes.customer import router as customer_router
from app.routes.auth import router as auth_router

app = FastAPI()


app.include_router(user_router)
app.include_router(food_router)
app.include_router(order_router)
app.include_router(customer_router)
app.include_router(auth_router)