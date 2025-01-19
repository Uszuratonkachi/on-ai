from dotenv import load_dotenv
import os

# Определяем путь к .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")

# Загружаем .env
load_dotenv(dotenv_path=env_path)

# Получаем переменные окружения
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Проверяем, загружены ли переменные
if not LLM_API_URL:
    raise ValueError("LLM_API_URL is not set. Please check your .env file.")
if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY is not set. Please check your .env file.")
