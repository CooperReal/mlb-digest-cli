import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import urlparse

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


@dataclass
class Article:
    title: str
    link: str
    summary: str
    source: str
    source_type: str  # "team" or "mlb"


@dataclass
class SelectedArticles:
    team: list[Article]
    mlb: list[Article]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_feed_content(url: str) -> str:
    response = httpx.get(
        url, timeout=10, follow_redirects=True, headers={"User-Agent": "mlb-digest-cli/1.0"}
    )
    response.raise_for_status()
    return response.text


def fetch_articles(feed_urls: list[str], source_type: str) -> list[Article]:
    articles: list[Article] = []

    for url in feed_urls:
        try:
            content = _fetch_feed_content(url)
        except Exception:
            logger.warning("Failed to fetch feed: %s", url, exc_info=True)
            continue

        feed = feedparser.parse(content)
        source = urlparse(url).netloc

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()

            if not title:
                continue

            articles.append(
                Article(
                    title=title,
                    link=link,
                    summary=summary,
                    source=source,
                    source_type=source_type,
                )
            )

    return articles


def deduplicate_articles(articles: list[Article]) -> list[Article]:
    seen: list[Article] = []

    for article in articles:
        normalized = article.title.lower().strip()
        is_duplicate = False

        for existing in seen:
            existing_normalized = existing.title.lower().strip()
            similarity = SequenceMatcher(None, normalized, existing_normalized).ratio()
            if similarity >= SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            seen.append(article)

    return seen


def select_articles(
    team_articles: list[Article],
    mlb_articles: list[Article],
    team_count: int = 2,
    mlb_count: int = 2,
) -> SelectedArticles:
    all_deduped = deduplicate_articles(team_articles + mlb_articles)

    team = [a for a in all_deduped if a.source_type == "team"][:team_count]
    mlb = [a for a in all_deduped if a.source_type == "mlb"][:mlb_count]

    return SelectedArticles(team=team, mlb=mlb)
