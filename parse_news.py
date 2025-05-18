import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os
import logging

# Налаштування логування
logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s - %(message)s')

# Джерела новин
SITES = [
    {
        "name": "forbes.ua",
        "url": "https://forbes.ua/news",
        "selector": "a.c-entry-link",
        "base_url": "https://forbes.ua"
    },
    {
        "name": "dou.ua",
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
        "Accept-Language": "uk-UA,uk;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Referer": "https://www.google.com/"
    }

    for site in SITES:
        try:
            print(f"Парсинг {site['name']}...")
            response = requests.get(site['url'], headers=headers, timeout=15)
            print(f"HTTP статус відповіді {site['name']}: {response.status_code}")

            if response.status_code != 200:
                print(f"⚠️ Помилка: {site['name']} повернув код {response.status_code}")
                if "Access Denied" in response.text or "Cloudflare" in response.text.lower():
                    print(f"⚠️ {site['name']} заблокував запит (Cloudflare або антибот захист)")
                logging.error(f"{site['name']} повернув код {response.status_code}")
                continue
            response.raise_for_status()

            time.sleep(2 if site['name'] == "forbes.ua" else 3)

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select(site['selector'])[:2]
            print(f"Знайдено статей для {site['name']}: {len(articles)}")

            if not articles:
                print(f"Попередження: Не знайдено статей за селектором {site['selector']}")
                logging.warning(f"Не знайдено статей за селектором {site['selector']}")
                continue

            for article in articles:
                title = article.get_text(strip=True)
                if not title:
                    print(f"Попередження: Порожній заголовок для {site['name']}")
                    continue
                link = article['href'] if article.has_attr('href') else site['url']
                if not link.startswith('http'):
                    link = site['base_url'] + link

                news_item = {
                    "source": site['name'],
                    "title": title,
                    "url": link,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                all_news.append(news_item)
                print(f"- {title[:60]}...")

        except requests.exceptions.HTTPError as e:
            print(f"Помилка HTTP для {site['name']}: {e}")
            logging.error(f"Помилка HTTP для {site['name']}: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Помилка з'єднання для {site['name']}: {e}")
            logging.error(f"Помилка з'єднання для {site['name']}: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Таймаут для {site['name']}: {e}")
            logging.error(f"Таймаут для {site['name']}: {e}")
        except Exception as e:
            print(f"Невідома помилка для {site['name']}: {e}")
            logging.error(f"Невідома помилка для {site['name']}: {e}")
            continue

    print(f"Всього зібрано новин: {len(all_news)}")
    os.makedirs("docs", exist_ok=True)
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        print(f"Новини збережено у {OUTPUT_FILE}")
    except Exception as e:
        print(f"Помилка збереження {OUTPUT_FILE}: {e}")
        logging.error(f"Помилка збереження {OUTPUT_FILE}: {e}")

    return all_news

if __name__ == "__main__":
    parse_news()
