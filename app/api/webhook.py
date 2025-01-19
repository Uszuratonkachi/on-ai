import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl
from app.services.llm import call_llm
from app.services.callback import send_to_callback
from app.models.webhook import WebhookRequest, LLMResponse
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import redis
import json
from os import getenv

# Настройка Redis
redis_client = redis.StrictRedis(
    host=getenv("REDIS_HOST", "localhost"),
    port=int(getenv("REDIS_PORT", 6379)),
    db=int(getenv("REDIS_DB", 0)),
    decode_responses=True
)

# Настройка лимитера
limiter = Limiter(key_func=get_remote_address)

# Глобальные переменные
MESSAGE_TTL = timedelta(hours=1)
MAX_REQUESTS = 100

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook", response_model=LLMResponse)
@limiter.limit("5/minute")  # Ограничение: 5 запросов в минуту на IP
async def handle_webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received request: {request.dict()}")

        if not request.callback_url:
            logger.error("callback_url is required but not provided.")
            raise HTTPException(status_code=400, detail="callback_url is required")

        # Генерируем ключ для хранения контекста
        context_key = f"context:{request.callback_url}"

        # Инициализация контекста
        if not redis_client.exists(context_key):
            redis_client.hset(context_key, mapping={
                "messages": json.dumps([]),
                "last_updated": datetime.utcnow().isoformat(),
                "request_count": 0
            })

        # Очистка устаревшего контекста
        cleanup_context(context_key)

        # Проверка лимита запросов
        context = redis_client.hgetall(context_key)
        if int(context["request_count"]) > MAX_REQUESTS:
            logger.error(f"Rate limit exceeded for {request.callback_url}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Добавление сообщения в контекст
        messages = json.loads(context["messages"])
        if request.message not in messages:
            messages.append(request.message)
            redis_client.hset(context_key, "messages", json.dumps(messages))
            redis_client.hset(context_key, "last_updated", datetime.utcnow().isoformat())

        redis_client.hincrby(context_key, "request_count", 1)

        # Вызов LLM API
        try:
            generated_response = await call_llm(request.message)
        except Exception as e:
            logger.error(f"Error during LLM API call: {e}")
            raise HTTPException(status_code=502, detail="Failed to process message with LLM")

        # Добавление ответа в контекст
        messages.append(generated_response)
        redis_client.hset(context_key, "messages", json.dumps(messages))
        redis_client.hset(context_key, "last_updated", datetime.utcnow().isoformat())

        # Формирование ответа
        response_data = {"response": generated_response}
        logger.info(f"Sending response to callback URL: {request.callback_url}")
        background_tasks.add_task(send_to_callback, str(request.callback_url), response_data)

        return response_data

    except RateLimitExceeded as e:
        # Обработка ошибки превышения лимита
        logger.error(f"Rate limit exceeded: {e.detail}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def cleanup_context(context_key: str):
    """Очистка старых данных из контекста в Redis."""
    context = redis_client.hgetall(context_key)
    if context and "last_updated" in context:
        last_updated = datetime.fromisoformat(context["last_updated"])
        if datetime.utcnow() - last_updated > MESSAGE_TTL:
            logger.info(f"Clearing outdated context for {context_key}")
            redis_client.delete(context_key)
