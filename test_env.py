from dotenv import load_dotenv
import os

load_dotenv()

print("LLM_API_URL:", os.getenv("LLM_API_URL"))
print("LLM_API_KEY:", os.getenv("LLM_API_KEY"))
