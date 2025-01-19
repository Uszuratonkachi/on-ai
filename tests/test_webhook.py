import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_webhook():
    """Test the /webhook endpoint."""
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Отправляем тестовый запрос
        response = await client.post("/webhook", json={
            "message": "Hello, bot!",
            "callback_url": "http://example.com/callback"
        })

    # Проверяем статус-код ответа
    assert response.status_code == 200

    # Проверяем, что ключ "response" существует в ответе
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)

@pytest.mark.asyncio
async def test_webhook_invalid_callback_url():
    """Test the /webhook endpoint with invalid callback_url."""
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Отправляем запрос с некорректным callback_url
        response = await client.post("/webhook", json={
            "message": "Hello, bot!",
            "callback_url": "httgps://webhook.site/example"
        })

    # Проверяем статус-код ответа
    assert response.status_code == 422

    # Проверяем содержимое ответа
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)

    # Проверяем, что ошибка содержит ожидаемые поля
    assert any(
        error.get("type") == "url_scheme" and
        error.get("msg") == "URL scheme should be 'http' or 'https'" and
        error.get("loc") == ["body", "callback_url"] and
        error.get("input") == "httgps://webhook.site/example" and
        error.get("ctx", {}).get("expected_schemes") == "'http' or 'https'"
        for error in data["detail"]
    )

    def test_redis_connection():
        import redis
        client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
        assert client.ping() == True

