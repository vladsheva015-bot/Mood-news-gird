import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

DATABASE = "news.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            published_at TEXT NOT NULL,
            original_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP        
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewritten_news(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            rewritten_content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news (id) ON DELETE CASCADE,
            UNIQUE(news_id, mood)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


def save_news_to_db(articles):
    conn = get_db_connection()
    cursor = conn.cursor()

    saved_count = 0
    for article in articles:
        cursor.execute("SELECT id FROM news WHERE url = ?", (article["url"],))
        existing = cursor.fetchone()

        if not existing:
            try:
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
            except sqlite3.Error as e:
                logger.warning(f"️ Не удалось сохранить статью: {e}")

    conn.commit()
    conn.close()
    logger.info(f"Сохранено {saved_count} новостей в БД")
    return saved_count


def get_news_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
           SELECT id, title, content, source, url, published_at
           FROM news
           ORDER BY published_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        # Преобразуем в список словарей
        news = []
        for row in rows:
            news.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "url": row["url"],
                "published_at": row["published_at"]
            })

        logger.info(f" Получено {len(news)} новостей из БД")
        if news:
            logger.info(f" Пример: {news[0]['title'][:50]}...")

        return news

    except sqlite3.Error as e:
        logger.error(f" Ошибка при получении новостей: {e}")
        conn.close()
        return []


def get_rewritten_news(news_id: int, mood: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
           SELECT rewritten_content
           FROM rewritten_news
           WHERE news_id = ?
             AND mood = ?
        ''', (news_id, mood))

        row = cursor.fetchone()
        conn.close()

        if row:
            logger.debug(f" Найдена версия '{mood}' для новости {news_id}")
            return row["rewritten_content"]
        else:
            logger.debug(f" Версия '{mood}' для новости {news_id} не найдена")
            return None

    except sqlite3.Error as e:
        logger.error(f" Ошибка при получении переписанной новости: {e}")
        conn.close()
        return None


def save_rewritten_news(news_id: int, mood: str, content: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO rewritten_news (news_id, mood, rewritten_content)
            VALUES (?, ?, ?)
        ''', (news_id, mood, content))

        conn.commit()
        conn.close()
        logger.info(f" Версия '{mood}' для новости {news_id} сохранена")

    except sqlite3.Error as e:
        logger.error(f" Ошибка при сохранении переписанной новости: {e}")
        conn.close()


def get_news_count() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM news")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error as e:
        logger.error(f" Ошибка при подсчёте новостей: {e}")
        conn.close()
        return 0


def get_news_by_id(news_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
           SELECT id, title, content, source, url, published_at
           FROM news
           WHERE id = ?
        ''', (news_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "url": row["url"],
                "published_at": row["published_at"]
            }
        return None

    except sqlite3.Error as e:
        logger.error(f" Ошибка при получении новости по ID: {e}")
        conn.close()
        return None