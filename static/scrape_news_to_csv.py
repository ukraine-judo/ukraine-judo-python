#!/usr/bin/env python3
"""scrape_news_to_csv.py

Scrape news articles from the Ukraine Judo Federation website and export them to CSV.

Key features:
• Starts from the listing page offset provided via ``--start`` (default 0).
• Automatically follows the "Вперед/Next" pagination links until exhaustion or
  the optional limits are reached.
• Extracts each article URL in chronological order (oldest to newest).
• Visits each article URL and collects: ID, title, publication
  date (ISO-formatted if possible), and full textual content (joined paragraphs).
• Writes UTF-8 CSV (comma-separated) with columns: ``id,title,date,url,html``.
• Writes UTF-8 JSON array ("news.json" by default) with objects containing:
  ``id``          – slugified title (latin letters)
  ``title``       – original title
  ``date``        – ISO date
  ``url``         – source URL
  ``html``        – cleaned article body
  ``category``    – predefined category list
  ``author_name`` – always "Пресс-служба ФДУ"
  ``excerpt``     – first ~160 символів тексту без HTML для превʼю
  ``featured``    – false (placeholder, можно выставлять вручную)
  ``image``       – локальный путь к превью (og:image або перше <img>)
  ``tags``        – сгенерированные ключевые слова

Usage (from project root):
    python scrape_news_to_csv.py            # default start=0 → news.json
    python scrape_news_to_csv.py out.csv    # custom output
    python scrape_news_to_csv.py --start 0 --max-pages 5 out.csv
    python scrape_news_to_csv.py --max-articles 12 out.csv  # first 12 articles
    python scrape_news_to_csv.py --end-article 100 out.csv  # up to 100th article
    python scrape_news_to_csv.py --start 0 --max-articles 10 out.json
    
Dependencies: ``requests`` and ``beautifulsoup4``.
Add them to your virtual-env with:
    pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup, Tag  # type: ignore
from urllib.parse import urljoin, urlparse
import os
import unicodedata

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
BASE = "https://ukrainejudo.com"
LIST_PATH = "/news"
LIST_URL = f"{BASE}{LIST_PATH}"
ARTICLE_RE = re.compile(r"/news/(\d+)-[\w\d-]+", re.IGNORECASE)

# Mapping of month names (ru + ua lower-case) → zero-padded month number
MONTH_MAP = {
    # Russian
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
    # Ukrainian
    "січня": "01",
    "лютого": "02",
    "березня": "03",
    "квітня": "04",
    "травня": "05",
    "червня": "06",
    "липня": "07",
    "серпня": "08",
    "вересня": "09",
    "жовтня": "10",
    "листопада": "11",
    "грудня": "12",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    )
}
TIMEOUT = 30

ASSETS_ROOT = Path("assets/news")

CATEGORY_LIST = [
    "achievements",
    "announcements",
    "greetings",
    "results",
    "decisions",
    "events",
    "partnerships",
    "federationNews",
    "competitions",
    "interviews",
    "education",
]

# Улучшенная система категоризации с приоритетами и весами
CATEGORY_RULES = {
    "greetings": {
        "priority": 1,  # Высший приоритет
        "title_keywords": [
            "вітаєм", "вітає", "поздравля", "поздравил", "з днем народження", 
            "з ювілеєм", "день народжен", "ювілей", "congratulat"
        ],
        "content_keywords": ["вітаєм", "поздравля", "ювілей", "день народжен"],
        "weight": 10,
    },
    "achievements": {
        "priority": 2,
        "title_keywords": [
            "золото", "срібло", "бронза", "медал", "чемпіон", "переможець", 
            "перемога", "нагород", "призер", "winning", "champion", "medal"
        ],
        "content_keywords": [
            "золот", "срібн", "бронз", "чемпіон", "перемог", "нагород", 
            "медал", "призер", "перше місце", "друге місце", "третє місце",
            "victory", "achievement"
        ],
        "weight": 8,
    },
    "results": {
        "priority": 3,
        "title_keywords": [
            "підсумки", "результат", "фінал", "турнірна таблиця", 
            "таблиця", "results", "final"
        ],
        "content_keywords": [
            "підсумк", "результат", "фінал", "турнірн", "таблиц",
            "перше місце", "друге місце", "третє місце"
        ],
        "weight": 7,
    },
    "competitions": {
        "priority": 4,
        "title_keywords": [
            "чемпіонат", "grand prix", "grand slam", "кубок", "open", 
            "masters", "першість", "змагання", "турнір", "championship"
        ],
        "content_keywords": [
            "чемпіонат", "grand", "slam", "prix", "кубок", "open", 
            "masters", "першість", "змагання", "турнір", "борців"
        ],
        "weight": 6,
    },
    "announcements": {
        "priority": 5,
        "title_keywords": [
            "увага", "анонс", "реєстрація", "запрошуєм", "запрошенн",
            "оголошення", "announcement", "registration"
        ],
        "content_keywords": [
            "увага", "анонс", "реєстрац", "запрош", "оголош", 
            "заяв", "прийм", "зареєструва"
        ],
        "weight": 7,
    },
    "decisions": {
        "priority": 6,
        "title_keywords": [
            "рішення", "постанова", "регламент", "правила", "протокол",
            "положення", "decision", "regulation"
        ],
        "content_keywords": [
            "рішення", "постанов", "регламент", "правил", "протокол",
            "положення", "затвердж"
        ],
        "weight": 6,
    },
    "federationNews": {
        "priority": 7,
        "title_keywords": [
            "федерація", "фду", "президент", "виконком", "комітет",
            "засідання", "federation", "president"
        ],
        "content_keywords": [
            "федераці", "фду", "президент", "виконком", "комітет",
            "засідання", "збори"
        ],
        "weight": 5,
    },
    "interviews": {
        "priority": 8,
        "title_keywords": [
            "інтерв'ю", "інтервью", "розмова", "бесіда", "говорить",
            "interview", "conversation"
        ],
        "content_keywords": [
            "інтерв", "розмов", "бесід", "говор", "запитання", "відповід"
        ],
        "weight": 8,
    },
    "partnerships": {
        "priority": 9,
        "title_keywords": [
            "партнер", "спонсор", "співпраця", "підтримка", "cooperation",
            "partner", "sponsor"
        ],
        "content_keywords": [
            "партнер", "спонсор", "співпрац", "підтримк", "cooperation"
        ],
        "weight": 6,
    },
    "education": {
        "priority": 10,
        "title_keywords": [
            "семінар", "курс", "навчання", "освіта", "академія", 
            "тренер", "coach", "education"
        ],
        "content_keywords": [
            "семінар", "курс", "навчан", "освіт", "академ", "тренер",
            "підготовк"
        ],
        "weight": 5,
    },
    "events": {
        "priority": 11,  # Найнижчий приоритет - default
        "title_keywords": [
            "подія", "захід", "зібрання", "event"
        ],
        "content_keywords": [
            "поді", "захід", "зібран", "event"
        ],
        "weight": 3,
    },
}

AUTHOR_NAME = "Пресс-служба ФДУ"

# Simple Ukrainian/Russian stopwords subset for tags
STOPWORDS = {
    "та", "і", "й", "в", "у", "з", "зі", "до", "на", "про", "за", "як", "що", "це", "але",
    "the", "and", "for", "with", "from", "this", "that", "а", "по", "від", "o", "або",
    "який", "яка", "яке", "який", "буде", "було", "став", "стала", "року", "році",
}

# Mapping для замены ссылок на протоколы и регламенты
PROTOCOL_LINKS = {
    "протокол": "https://ukraine-judo.github.io/protocols.html",
    "protocol": "https://ukraine-judo.github.io/protocols.html",
    "регламент": "https://ukraine-judo.github.io/regulations.html",
    "regulation": "https://ukraine-judo.github.io/regulations.html",
    "положення": "https://ukraine-judo.github.io/regulations.html",
}

# Глобальный словарь для хранения всех статей (для внутренних ссылок)
ALL_ARTICLES_MAP: Dict[str, str] = {}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def fetch_soup(url: str) -> BeautifulSoup:
    """Download *url* and return parsed *BeautifulSoup* object."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
    except Exception as exc:
        sys.exit(f"Error fetching {url}: {exc}")
    return BeautifulSoup(res.text, "html.parser")


def normalise_date(raw: str) -> str:
    """Convert strings like '14 февраля, 2025' into '2025-02-14'.

    If parsing fails, return *raw* unchanged.
    """
    m = re.search(r"(\d{1,2})\s+([\wА-Яа-яёЁЇїІіЄєҐґ]+).*?(\d{4})", raw)
    if not m:
        return raw.strip()
    day, month_name, year = m.groups()
    month = MONTH_MAP.get(month_name.lower())
    if not month:
        return raw.strip()
    return f"{year}-{month}-{int(day):02d}"


def extract_article_links(soup: BeautifulSoup) -> List[str]:
    """Return a list of unique article hrefs from a listing *soup* (newest first on page)."""
    hrefs: List[str] = []
    seen: Set[str] = set()
    for a in soup.find_all("a", href=True):
        match = ARTICLE_RE.search(a["href"])
        if match:
            href = a["href"]
            # Ensure absolute URL
            if href.startswith("/"):
                href = f"{BASE}{href}"
            if href not in seen:
                hrefs.append(href)
                seen.add(href)
    # Return in order as they appear on page
    return hrefs


def find_next_page(soup: BeautifulSoup) -> Optional[str]:
    """Locate the 'Next/Вперед' pagination link, return URL or *None*."""
    link = soup.find("a", string=re.compile("Вперед|Next", re.IGNORECASE))
    if link and link.has_attr("href"):
        href = link["href"]
        return f"{BASE}{href}" if href.startswith("/") else href
    return None


def ensure_download_image(src_url: str, year: str, month: str) -> str:
    """Download *src_url* into assets/news/<year>/<month>/ and return relative path."""
    parsed = urlparse(src_url)
    filename = os.path.basename(parsed.path)
    save_dir = ASSETS_ROOT / year / month
    save_dir.mkdir(parents=True, exist_ok=True)
    dest_path = save_dir / filename

    if not dest_path.exists():
        try:
            resp = requests.get(src_url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            dest_path.write_bytes(resp.content)
            print(f"      ↓ image {filename} → {dest_path}")
        except Exception as exc:
            print(f"      ⚠️  image download failed {src_url}: {exc}")

    # Return POSIX-style relative path
    return str(dest_path.as_posix())


def fix_internal_links(body: Tag) -> None:
    """Заменяет внутренние ссылки на украinејудо на наши ссылки."""
    for a in body.find_all("a", href=True):
        href = a["href"]
        
        # Проверяем, является ли ссылка внутренней статьей ukrainejudo.com
        if "ukrainejudo.com/news/" in href or href.startswith("/news/"):
            match = ARTICLE_RE.search(href)
            if match:
                article_id = match.group(1)
                # Проверяем, есть ли эта статья в нашем списке
                if article_id in ALL_ARTICLES_MAP:
                    new_href = f"/news/{ALL_ARTICLES_MAP[article_id]}"
                    a["href"] = new_href
                    print(f"        ↻ internal link: {href} → {new_href}")
                    continue
        
        # Проверяем ссылки на протоколы и регламенты
        link_text = a.get_text(strip=True).lower()
        for keyword, new_url in PROTOCOL_LINKS.items():
            if keyword in link_text or keyword in href.lower():
                a["href"] = new_url
                print(f"        ↻ protocol/regulation link: {href} → {new_url}")
                break


def clean_and_localise_html(body: Tag, year: str, month: str) -> str:
    """Remove style attrs, download images, update src paths, fix links, return HTML."""
    # Remove style attributes
    for tag in body.find_all(True):
        if "style" in tag.attrs:
            del tag.attrs["style"]

    # Process images
    for img in body.find_all("img", src=True):
        src = img["src"].strip().strip('"\'')
        src = src.rstrip('/')
        abs_url = src if src.startswith("http") else urljoin(BASE, src)
        local_path = ensure_download_image(abs_url, year, month)
        # Convert to relative path from project root (use forward slashes)
        img["src"] = local_path

    # Fix internal links and protocol/regulation links
    fix_internal_links(body)

    html_output = body.decode_contents()
    # Collapse whitespace/newlines between tags
    html_output = re.sub(r">\s+<", "><", html_output)
    html_output = re.sub(r"\n+", "", html_output)
    # Replace src="..." with src='...' for cleaner JSON representation
    html_output = re.sub(r'src="([^"]+)"', r"src='\1'", html_output)
    return html_output


def slugify(text: str) -> str:
    """Convert *text* to lowercase Latin slug (letters, numbers, hyphens)."""
    # Transliteration mapping for Ukrainian & Russian
    mapping = {
        # Ukrainian / Russian common
        "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
        "є": "ye", "ё": "yo", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi",
        "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
        "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "shch", "ь": "", "ы": "y", "ъ": "", "э": "e",
        "ю": "yu", "я": "ya",
    }
    # Normalize and transliterate
    text = unicodedata.normalize("NFKD", text.lower())
    translit = "".join(mapping.get(ch, ch) for ch in text)
    # Replace non-alphanum with hyphen
    translit = re.sub(r"[^a-z0-9]+", "-", translit)
    # Collapse multiple hyphens & trim
    translit = re.sub(r"-{2,}", "-", translit).strip("-")
    return translit or "untitled"


def choose_category(title: str, text: str) -> str:
    """Улучшенная категоризация с весами и приоритетами."""
    title_lower = title.lower()
    text_lower = text.lower()
    
    # Словарь для хранения оценок по каждой категории
    scores: Dict[str, float] = {}
    
    for category, rules in CATEGORY_RULES.items():
        score = 0.0
        
        # Проверяем ключевые слова в заголовке (больший вес)
        title_matches = sum(1 for kw in rules["title_keywords"] if kw in title_lower)
        score += title_matches * rules["weight"] * 2  # Заголовок важнее
        
        # Проверяем ключевые слова в тексте
        content_matches = sum(1 for kw in rules["content_keywords"] if kw in text_lower)
        score += content_matches * rules["weight"]
        
        if score > 0:
            # Учитываем приоритет категории (меньше = выше приоритет)
            # Вычитаем небольшое значение, чтобы при равных оценках выиграл более приоритетный
            adjusted_score = score - (rules["priority"] * 0.1)
            scores[category] = adjusted_score
    
    # Выбираем категорию с максимальной оценкой
    if scores:
        best_category = max(scores.items(), key=lambda x: x[1])[0]
        return best_category
    
    # По умолчанию возвращаем "events"
    return "events"


def extract_tags(title: str, text: str, limit: int = 5) -> list[str]:
    """Return up to *limit* keywords from title/text (deduplicated)."""
    words = re.findall(r"[\w'']+", f"{title} {text}")
    tags: list[str] = []
    for w in words:
        wl = w.lower()
        if len(wl) < 4 or wl in STOPWORDS:
            continue
        if wl not in tags:
            tags.append(wl)
        if len(tags) >= limit:
            break
    return tags


def make_excerpt(text: str, length: int = 160) -> str:
    """Return truncated text at word boundary not exceeding *length*."""
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(" ", 1)[0]
    return f"{cut}…"


def find_preview_src(soup: BeautifulSoup, body: Optional[Tag]) -> Optional[str]:
    """Return absolute URL of preview image if available."""
    # 1) og:image
    meta = soup.find("meta", property="og:image")
    if meta and meta.get("content"):
        return meta["content"].strip()

    # 2) twitter:image
    meta = soup.find("meta", property="twitter:image")
    if meta and meta.get("content"):
        return meta["content"].strip()

    # 3) first img in article body
    if body:
        img = body.find("img", src=True)
        if img:
            return img["src"].strip().strip('"\'').rstrip('/')
    return None


def parse_article(url: str) -> Dict[str, str]:
    """Extract details from an article URL into a dict."""
    soup = fetch_soup(url)

    # Title – try <h2.page-header>, <h1>, or first <title>
    title_tag: Optional[Tag] = soup.find("h2", class_=re.compile("header", re.I)) or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else soup.title.get_text(strip=True)

    # Publication date – look for <time>, Joomla span classes, meta tag…
    date_tag = (
        soup.find("time")
        or soup.find("span", class_=re.compile("date|created", re.I))
        or soup.find("meta", attrs={"property": "article:published_time"})
    )
    if date_tag:
        date_raw = date_tag.get("content") if date_tag.name == "meta" else date_tag.get_text(strip=True)
    else:
        date_raw = ""
    date = normalise_date(date_raw)

    # Determine month for assets folder from date
    m_date = re.match(r"(\d{4})-(\d{2})-", date)
    year_str, month_str = (m_date.group(1), m_date.group(2)) if m_date else ("2025", "01")

    # Main text – common Joomla selectors
    body = (
        soup.find("div", class_=re.compile("itemFullText|entry-content|article-body|content", re.I))
        or soup.find("div", class_=re.compile("article-content", re.I))
    )
    html_content = clean_and_localise_html(body, year_str, month_str) if body else ""

    plain_text = body.get_text(" ", strip=True) if body else ""

    category = choose_category(title, plain_text)
    tags = extract_tags(title, plain_text)

    excerpt = make_excerpt(plain_text, 160)

    # Preview image
    preview_src = find_preview_src(soup, body)
    if preview_src:
        abs_preview = preview_src if preview_src.startswith("http") else urljoin(BASE, preview_src)
        preview_path = ensure_download_image(abs_preview, year_str, month_str)
    else:
        preview_path = ""

    # Article ID – slugified title
    article_id = slugify(title)
    
    # Извлекаем числовой ID из URL для маппинга внутренних ссылок
    url_match = ARTICLE_RE.search(url)
    if url_match:
        numeric_id = url_match.group(1)
        ALL_ARTICLES_MAP[numeric_id] = article_id

    return {
        "id": article_id,
        "title": title,
        "date": date,
        "url": url,
        "html": html_content,
        "category": category,
        "author_name": AUTHOR_NAME,
        "excerpt": excerpt,
        "featured": False,
        "image": preview_path,
        "tags": tags,
    }

# ---------------------------------------------------------------------------
# Main scraping routine
# ---------------------------------------------------------------------------

def _extract_start_offset(url: str) -> Optional[int]:
    m = re.search(r"[?&]start=(\d+)", url)
    return int(m.group(1)) if m else None


def scrape(
    start: int, 
    max_pages: Optional[int] = None, 
    max_articles: Optional[int] = None, 
    end_article: Optional[int] = None
) -> Tuple[List[Dict[str, str]], int, int]:
    """Scrape starting from *start* offset.

    Args:
        start: Starting page offset (0 = first page with oldest articles)
        max_pages: Maximum number of pages to visit
        max_articles: Maximum number of articles to scrape
        end_article: Stop scraping when this article number is reached (1-indexed)

    Returns tuple: (records list, last_start_offset, pages_processed)
    """
    records: List[Dict[str, str]] = []
    seen_links: Set[str] = set()

    page_url = f"{LIST_URL}?start={start}"
    pages_processed = 0
    last_offset = start
    article_count = 0

    while page_url and (max_pages is None or pages_processed < max_pages):
        pages_processed += 1
        current_offset = _extract_start_offset(page_url) or last_offset
        last_offset = current_offset
        print(f"→ Listing page {pages_processed} (start={current_offset}): {page_url}")

        soup = fetch_soup(page_url)

        links = extract_article_links(soup)
        if not links:
            print("  ⚠️  No article links found – stopping.")
            break

        for link in links:
            # Check if we've reached article limits
            article_count += 1
            
            if (max_articles is not None and article_count > max_articles) or \
               (end_article is not None and article_count > end_article):
                print(f"✓ Reached article limit: {article_count - 1}")
                return records, last_offset, pages_processed

            if link in seen_links:
                continue
            seen_links.add(link)
            
            try:
                data = parse_article(link)
                records.append(data)
                print(f"    ✓ {data['id']}: {data['title'][:60]} | Category: {data['category']} (Article {article_count})")
            except Exception as exc:
                print(f"    ⚠️  Failed {link}: {exc}")

        # Pagination – next page
        page_url = find_next_page(soup)

    return records, last_offset, pages_processed


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:  # noqa: D401
    p = argparse.ArgumentParser(description="Scrape Ukraine Judo news to JSON")
    p.add_argument(
        "output",
        nargs="?",
        default="news.json",
        help="Destination JSON file path (default: news.json)",
    )
    p.add_argument("--start", type=int, default=0, help="Offset for first listing page (default 0 - oldest articles)")
    p.add_argument("--max-pages", type=int, dest="max_pages", help="Maximum listing pages to visit")
    p.add_argument("--max-articles", type=int, dest="max_articles", help="Maximum number of articles to scrape")
    p.add_argument("--end-article", type=int, dest="end_article", help="Stop scraping after this article number (1-indexed)")
    return p.parse_args()


def write_json(rows: List[Dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✔ Saved {len(rows)} articles → {path}")


def main() -> None:  # noqa: D401
    args = parse_args()
    rows, last_offset, pages_processed = scrape(
        start=args.start, 
        max_pages=args.max_pages, 
        max_articles=args.max_articles, 
        end_article=args.end_article
    )
    write_json(rows, Path(args.output))
    print(f"✔ Scraped {pages_processed} pages, last start offset: {last_offset}")


if __name__ == "__main__":
    main()
