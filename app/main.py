from fastapi import FastAPI
from redis import StrictRedis
from app.api import webhook
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from os import getenv
from redis import StrictRedis

# Загрузка .env файла
load_dotenv()

# Подключение к Redis
redis_client = StrictRedis(
    host=getenv("REDIS_HOST", "localhost"),
    port=int(getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Создаем Limiter с использованием Redis
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")

# Создаем FastAPI приложение
app = FastAPI(
    title="LLM Webhook API",
    description="A REST API for processing webhook requests with LLM integration."
)

# Добавляем middleware для обработки rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Подключаем роутеры
app.include_router(webhook.router)

# Проверка подключения к Redis при старте приложения
@app.on_event("startup")
async def test_redis_connection():
    try:
        redis_client.ping()
        print("Redis connection successful!")
    except Exception as e:
        print(f"Redis connection failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
