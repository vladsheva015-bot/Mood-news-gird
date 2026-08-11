import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.database import init_db, get_db_connection
from app.services.news_fetcher import fetch_news
from app.services.ai_processor import rewrite_news
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Mood News Grid")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def save_news_to_db(articles):
    conn = get_db_connection()
    cursor = conn.cursor()

    saved_count = 0
    for article in articles:
        cursor.execute("SELECT id FROM news WHERE url = ?", (article["url"],))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute('''
                INSERT INTO news (title, content, source, url, published_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
               article["title"],
               article["content"],
               article["source"],
               article["url"],
               article["published_at"]
            ))
            saved_count += 1

    conn.commit()
    conn.close()
    return saved_count


def get_news_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
       SELECT id, title, content, source, url, published_at
       FROM news
       ORDER BY published_at DESC
    ''')

    news = cursor.fetchall()
    conn.close()

    return [dict(row) for row in news]


def get_rewritten_news(news_id: int, mood: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
       SELECT rewritten_content
       FROM rewritten_news
       WHERE news_id = ?
         AND mood = ?
    ''', (news_id, mood))

    row = cursor.fetchone()
    conn.close()

    return row["rewritten_content"] if row else None


def save_rewritten_news(news_id: int, mood: str, content: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO rewritten_news (news_id, mood, rewritten_content)
        VALUES (?, ?, ?)
    ''', (news_id, mood, content))

    conn.commit()
    conn.close()


async def ensure_news_loaded():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM news")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        logger.info("Новостей в БД нет. Загружаем...")
        try:
            articles = await fetch_news()
            if articles:
                saved = save_news_to_db(articles)
                logger.info(f"Загружено {saved} новостей")

                await generate_rewrites_for_news()
            else:
                logger.warning("Не удалось загрузить новости")
        except Exception as e:
            logger.error(f"Ошибка загрузки новостей: {e}")
    else:
        logger.info(f"В БД уже есть {count} новостей")


async def generate_rewrites_for_news():
    news = get_news_from_db()

    for item in news:
        news_id = item["id"]
        content = item["content"]

        for mood in Config.MOODS:
            existing = get_rewritten_news(news_id, mood)
            if existing:
                continue

            logger.info(f"Генерируем версию '{mood}' для новости {news_id}")
            rewritten = await rewrite_news(content, mood)

            if rewritten:
                save_rewritten_news(news_id, mood, rewritten)
                logger.info(f" Версия '{mood}' сохранена")
            else:
                logger.warning(f" Не удалось сгенерировать '{mood}'")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("База данных инициализирована")

    await ensure_news_loaded()


@app.get("/")
async def index(request: Request):
    news = get_news_from_db()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "moods": Config.MOODS,
        "news": news
    })


@app.get("/api/news/{news_id}/{mood}")
async def get_news_with_mood(news_id: int, mood: str):
    if mood not in Config.MOODS:
        raise HTTPException(status_code=400, detail="Неизвестное настроение")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
       SELECT id, title, content, source, url, published_at
       FROM news
       WHERE id = ?
    ''', (news_id,))

    news = cursor.fetchone()
    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    rewritten = get_rewritten_news(news_id, mood)

    if not rewritten:
        rewritten = await rewrite_news(news["content"], mood)
        if rewritten:
            save_rewritten_news(news_id, mood, rewritten)

    conn.close()

    return {
        "original": {
            "title": news["title"],
            "content": news["content"],
            "source": news["source"],
            "url": news["url"],
            "published_at": news["published_at"]
        },
        "rewritten": rewritten or "Не удалось переписать новость",
        "mood": mood
    }


@app.get("/api/refresh")
async def refresh_news():
    try:
        articles = await fetch_news()
        if articles:
            saved = save_news_to_db(articles)
            await generate_rewrites_for_news()
            return {"status": "ok", "saved": saved}
        return {"status": "error", "message": "Не удалось загрузить новости"}
    except Exception as e:
        return {"status": "error", "message": str(e)}