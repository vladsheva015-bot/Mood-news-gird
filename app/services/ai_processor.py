import httpx
from typing import Optional
from config import Config
import logging

logger = logging.getLogger(__name__)


def build_prompt(content: str, mood: str) -> str:
    mood_descriptions = {
        "neutral": "нейтрально, без эмоций, только факты",
        "positive": "позитивно, оптимистично, с акцентом на хорошее",
        "sad": "грустно, пессимистично, с акцентом на проблемы",
        "ironic": "иронично, с лёгкой насмешкой",
        "inspiring": "вдохновляюще, мотивирующе"
    }

    return f"""
    Твоя задача — переписать новость в заданном настроении.

    ВАЖНО: СОХРАНИ ВСЕ ФАКТЫ:
    - Имена людей и организаций
    - Даты и числа
    - Места и географические названия
    - Прямые цитаты (если есть)

    НЕЛЬЗЯ:
    - Добавлять вымышленные детали
    - Удалять факты
    - Менять смысл происходящего

    Настроение: {mood_descriptions.get(mood, "нейтрально")}

    Новость:
    {content}

    Перепиши новость в заданном настроении. Сохрани все факты.
    """


async def rewrite_news(content: str, mood: str) -> Optional[str]:
    if not Config.YANDEX_API_KEY or not Config.YANDEX_FOLDER_ID:
        logger.error(" YandexGPT не настроен (нет ключа или folder_id)")
        return None

    prompt = build_prompt(content, mood)

    model_uri = f"gpt://{Config.YANDEX_FOLDER_ID}/yandexgpt-lite/latest"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                Config.YANDEX_API_URL,
                headers={
                    "Authorization": f"Api-Key {Config.YANDEX_API_KEY}",
                    "x-folder-id": Config.YANDEX_FOLDER_ID,
                    "Content-Type": "application/json"
                },
                json={
                    "modelUri": model_uri,
                    "completionOptions": {
                        "temperature": 0.7,
                        "maxTokens": 1000
                    },
                    "messages": [
                        {
                            "role": "system",
                            "text": "Ты — помощник, который переписывает новости, сохраняя все факты."
                        },
                        {
                            "role": "user",
                            "text": prompt
                        }
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"YandexGPT ошибка: {response.status_code}")
                logger.error(f"Ответ: {response.text}")
                return None

            data = response.json()
            result = data["result"]["alternatives"][0]["message"]["text"]
            logger.info(f"YandexGPT успешно обработал новость")
            return result

    except Exception as e:
        logger.error(f"Ошибка YandexGPT: {e}")
        return None