import httpx
from datetime import datetime
from typing import List, Dict
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://lenta.ru/rss",
    "https://ria.ru/export/rss2/archive/index.html",
    "https://www.rbc.ru/rss/",
    "https://tass.ru/rss/v2.xml",
    "https://vz.ru/rss.xml",
    "https://iz.ru/xml/rss/all.xml"
]


async def fetch_news_from_rss() -> List[Dict]:
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            logger.info(f"Загружаем RSS: {feed_url}")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(feed_url)

                if response.status_code != 200:
                    logger.warning(f"Не удалось загрузить RSS: {feed_url} (статус {response.status_code})")
                    continue

                root = ET.fromstring(response.text)

                for item in root.findall(".//item"):
                    title = item.find("title")
                    title_text = title.text.strip() if title is not None and title.text else ""

                    description = item.find("description")
                    description_text = description.text.strip() if description is not None and description.text else ""

                    content = description_text if description_text and len(description_text) > 20 else title_text

                    if not content or len(content) < 20:
                        continue

                    link = item.find("link")
                    link_url = link.text.strip() if link is not None and link.text else ""

                    pub_date = item.find("pubDate")
                    pub_date_text = pub_date.text.strip() if pub_date is not None and pub_date.text else datetime.now().isoformat()

                    source = feed_url.replace("https://", "").replace("http://", "").split("/")[0]

                    articles.append({
                        "title": title_text if title_text else "Новость",
                        "content": content,
                        "source": source,
                        "url": link_url,
                        "published_at": pub_date_text
                    })

                    if len(articles) >= 10:
                        break

                logger.info(f"✅ Из {feed_url} получено {len(articles)} статей")

        except Exception as e:
            logger.warning(f"❌ Ошибка при загрузке {feed_url}: {e}")
            continue

    return articles[:10]


async def fetch_news() -> List[Dict]:
    logger.info("📡 Загружаем новости из RSS-лент...")
    articles = await fetch_news_from_rss()

    if articles:
        logger.info(f"Получено {len(articles)} статей из RSS")
    else:
        logger.warning("Не удалось получить новости из RSS")

    return articles