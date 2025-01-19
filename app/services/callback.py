import httpx

async def send_to_callback(url: str, response: dict):
    """Send the LLM response to the callback URL."""
    async with httpx.AsyncClient() as client:
        try:
            # Преобразование HttpUrl в строку
            url = str(url)
            await client.post(url, json=response)
        except httpx.RequestError as exc:
            print(f"Error sending callback: {exc}")
