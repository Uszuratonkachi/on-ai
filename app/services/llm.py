async def call_llm(message: str) -> str:
    import os
    import httpx

    llm_api_url = os.getenv("LLM_API_URL")
    llm_api_key = os.getenv("LLM_API_KEY")

    # Логирование
    print(f"LLM_API_URL inside call_llm: {llm_api_url}")
    print(f"LLM_API_KEY inside call_llm: {llm_api_key[:10]}...")

    if not llm_api_url or not llm_api_key:
        raise ValueError("LLM_API_URL or LLM_API_KEY is not set.")

    headers = {"Authorization": f"Bearer {llm_api_key}"}
    payload = {
        "messages": [{"role": "user", "content": message}],
        "model": "gpt-3.5-turbo"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(llm_api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
