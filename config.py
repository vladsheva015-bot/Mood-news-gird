import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
    YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
    YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    MAX_NEWS = 10
    MOODS = ["neutral", "positive", "sad", "ironic", "inspiring"]
    LANGUAGE = "ru"