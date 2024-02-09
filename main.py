from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import contacts, auth
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from database import engine
from redis import Redis
from rq import Queue, Worker
import os

load_dotenv()

app = FastAPI()

# Налаштування CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Налаштування обмежувача швидкості
limiter = FastAPILimiter(key_func=contacts.get_current_user, redis_url="redis://localhost:6379/1")
app.state.limiter = limiter

# Підключення до Redis
redis = Redis(host='localhost', port=6379)

# Створення черги задач для Redis
q = Queue(connection=redis)

# Запуск робітника Redis
worker = Worker([q], connection=redis)
worker.work()

# Підключення роутерів
app.include_router(contacts.router, tags=["contacts"])
app.include_router(auth.router, tags=["auth"])
