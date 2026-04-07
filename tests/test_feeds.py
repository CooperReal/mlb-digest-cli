import logging
from pathlib import Path
from unittest.mock import patch

from mlb_digest.feeds import (
    Article,
    deduplicate_articles,
    fetch_articles,
    select_articles,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_rss_feed_returns_articles():
    feed_xml = (FIXTURES / "team_feed.xml").read_text()

    with patch("mlb_digest.feeds._fetch_feed_content", return_value=feed_xml):
        articles = fetch_articles(["https://example.com/feed"], source_type="team")

    assert len(articles) == 3
    assert articles[0].title == "Braves Sign New Closer in Blockbuster Deal"
    assert articles[0].link == "https://www.mlbtraderumors.com/braves-closer"
    assert articles[0].source_type == "team"
    assert len(articles[0].summary) > 0


def test_empty_feed_returns_no_articles():
    feed_xml = (FIXTURES / "empty_feed.xml").read_text()

    with patch("mlb_digest.feeds._fetch_feed_content", return_value=feed_xml):
        articles = fetch_articles(["https://example.com/feed"], source_type="team")

    assert articles == []


def test_deduplicate_removes_similar_titles():
    articles = [
        Article(
            title="Braves Sign New Closer in Blockbuster Deal",
            link="https://example.com/a",
            summary="First source version.",
            source="example.com",
            source_type="team",
        ),
        Article(
            title="Braves Sign New Closer in Blockbuster Deal",
            link="https://example.com/b",
            summary="Second source version.",
            source="other.com",
            source_type="mlb",
        ),
        Article(
            title="MLB Announces Rule Changes for 2026 Season",
            link="https://example.com/c",
            summary="Different article entirely.",
            source="mlb.com",
            source_type="mlb",
        ),
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 2
    titles = [a.title for a in result]
    assert "MLB Announces Rule Changes for 2026 Season" in titles


def test_failed_feed_logs_warning_and_returns_empty(caplog):
    with (
        caplog.at_level(logging.WARNING),
        patch(
            "mlb_digest.feeds._fetch_feed_content",
            side_effect=Exception("Connection refused"),
        ),
    ):
        articles = fetch_articles(
            ["https://broken.example.com/feed"],
            source_type="team",
        )

    assert articles == []
    assert "Connection refused" in caplog.text


def test_fetch_articles_from_multiple_feeds():
    team_xml = (FIXTURES / "team_feed.xml").read_text()
    mlb_xml = (FIXTURES / "mlb_feed.xml").read_text()

    def mock_fetch(url: str) -> str:
        if "team" in url:
            return team_xml
        return mlb_xml

    with patch("mlb_digest.feeds._fetch_feed_content", side_effect=mock_fetch):
        articles = fetch_articles(
            ["https://example.com/team", "https://example.com/mlb"],
            source_type="team",
        )

    assert len(articles) == 6


def test_select_articles_separates_by_source_type():
    team_articles = [
        Article(
            title="Team A",
            link="https://a.com/1",
            summary="a",
            source="a.com",
            source_type="team",
        ),
        Article(
            title="Team B",
            link="https://a.com/2",
            summary="b",
            source="a.com",
            source_type="team",
        ),
        Article(
            title="Team C",
            link="https://a.com/3",
            summary="c",
            source="a.com",
            source_type="team",
        ),
    ]
    mlb_articles = [
        Article(
            title="MLB A",
            link="https://b.com/1",
            summary="a",
            source="b.com",
            source_type="mlb",
        ),
        Article(
            title="MLB B",
            link="https://b.com/2",
            summary="b",
            source="b.com",
            source_type="mlb",
        ),
        Article(
            title="MLB C",
            link="https://b.com/3",
            summary="c",
            source="b.com",
            source_type="mlb",
        ),
    ]

    result = select_articles(team_articles, mlb_articles, team_count=2, mlb_count=2)

    assert len(result.team) == 2
    assert len(result.mlb) == 2
    assert all(a.source_type == "team" for a in result.team)
    assert all(a.source_type == "mlb" for a in result.mlb)


def test_select_articles_deduplicates_across_feeds():
    team_articles = [
        Article(
            title="Same Story",
            link="https://a.com/1",
            summary="a",
            source="a.com",
            source_type="team",
        ),
    ]
    mlb_articles = [
        Article(
            title="Same Story",
            link="https://b.com/1",
            summary="a",
            source="b.com",
            source_type="mlb",
        ),
        Article(
            title="Different Story",
            link="https://b.com/2",
            summary="b",
            source="b.com",
            source_type="mlb",
        ),
    ]

    result = select_articles(team_articles, mlb_articles, team_count=2, mlb_count=2)

    all_titles = [a.title for a in result.team + result.mlb]
    assert all_titles.count("Same Story") == 1
