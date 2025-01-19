from pydantic import BaseModel, HttpUrl

class WebhookRequest(BaseModel):
    message: str
    callback_url: HttpUrl

class LLMResponse(BaseModel):
    response: str