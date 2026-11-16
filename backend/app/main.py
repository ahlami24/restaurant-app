from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routes.auth import router as auth_router
from app.routes.customer import router as customer_router
from app.routes.food import router as food_router
from app.routes.order import router as order_router
from app.routes.restaurant import router as restaurant_router
from app.routes.user import router as user_router

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.include_router(user_router)
app.include_router(customer_router)
app.include_router(food_router)
app.include_router(order_router)
app.include_router(auth_router)
app.include_router(restaurant_router)