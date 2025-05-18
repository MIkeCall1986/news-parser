import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os
import logging

logging.basicConfig(filename='errors.log', level=logging.ERROR)

SITES = [
    {
        "name": "Forbes.ua",
        "url": "https://forbes.ua/news",
        "selector": "a.c-entry-link",
        "base_url": "https://forbes.ua"
    },
    {
        "name": "DOU.ua",
        "url": "https://dou.ua/lenta/",
        "selector": "a.link[href*='/lenta/news/']",
        "base_url": "https://dou.ua"
    }
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
OUTPUT_FILE = "docs/news.json"

def parse_news():
    all_news = []
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "uk-UA,uk;q=0.9"
    }

    # Перевірка і створення папки docs
    if not os.path.exists("docs"):
        os.mkdir("docs")
        print("Створено папку docs")
    else:
        print("Папка docs уже існує")

    for site in SITES:
        try:
            print(f"Парсимо {site['name']}...")
            response = requests.get(site['url'], headers=headers, timeout=15)
            print(f"HTTP статус відповіді {site['name']}: {response.status_code}")
            if response.status_code != 200:
                print(f"⚠️ Помилка: {site['name']} повернув код {response.status_code}")
                if "Access Denied" in response.text or "Cloudflare" in response.text.lower():
                    print(f"⚠️ {site['name']} заблокував запит (Cloudflare або антибот захист)")
                logging.error(f"{site['name']} повернув код {response.status_code}")
                continue
            response.raise_for_status()
            time.sleep(2)

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select(site['selector'])[:2]
            print(f"Знайдено статей для {site['name']}: {len(articles)}")
            if not articles:
                raise ValueError(f"Не знайдено статей за селектором: {site['selector']}")

            for article in articles:
                title = article.get_text(strip=True)
                link = article['href'] if article.has_attr('href') else site['url']
                if not link.startswith('http'):
                    link = site['base_url'] + link

                all_news.append({
                    "site": site['name'],
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat() + "Z"
                })
                print(f"- {title[:60]}...")

        except Exception as e:
            print(f"Помилка у {site['name']}: {str(e)}")
            logging.error(f"Помилка у {site['name']}: {str(e)}")
            continue

    print(f"Зібрано новин: {len(all_news)}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    print(f"Перезаписано файл {OUTPUT_FILE}")
    return all_news

if __name__ == "__main__":
    parse_news()
