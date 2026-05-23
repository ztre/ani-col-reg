import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.html_parsing import (
    clean_multiline_text as _clean_multiline_text,
    collapse_whitespace as _collapse_whitespace,
    find_section_heading as _find_section_heading,
    first_non_empty as _first_non_empty,
    meta_content as _meta_content,
    section_nodes as _section_nodes,
)


SEASON_MONTH = {1: "01", 2: "04", 3: "07", 4: "10"}


@dataclass
class AnimeSourceRecord:
    title_cn: str
    source_id: str | None
    source_url: str | None
    year: int
    season: int
    title_jp: str | None = None
    title_en: str | None = None
    aliases: str | None = None
    synopsis: str | None = None
    premiere_date: str | None = None
    platforms: str | None = None
    staff: str | None = None
    cast: str | None = None
    tags: str | None = None
    pv_url: str | None = None
    cover_url: str | None = None


def normalize_title(title: str) -> str:
    return "".join(title.lower().split())


def season_url(base_url: str, year: int, season: int) -> str:
    month = SEASON_MONTH[season]
    return f"{base_url.rstrip('/')}/bangumi/{year}{month}"


class YourAnimesScraper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
        url = season_url(self.base_url, year, season)
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        return parse_season_html(response.text, self.base_url, year, season)

    async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord | None:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(source_url)
            response.raise_for_status()
        return parse_detail_html(response.text, self.base_url, source_url, fallback=fallback)


def parse_season_html(html: str, base_url: str, year: int, season: int) -> list[AnimeSourceRecord]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = _candidate_blocks(soup)
    records: list[AnimeSourceRecord] = []
    seen: set[str] = set()

    for block in candidates:
        link = _best_link(block)
        title = _title_from_block(block, link)
        if not title:
            continue

        href = link.get("href") if link else None
        source_url = urljoin(base_url, href) if href else None
        source_id = _source_id_from_url(source_url) or normalize_title(title)
        cover_url = _cover_url_from_block(block, link, base_url)
        key = source_url or f"{year}-{season}-{normalize_title(title)}"
        if key in seen:
            continue
        seen.add(key)

        text = " ".join(block.get_text(" ", strip=True).split())
        records.append(
            AnimeSourceRecord(
                title_cn=title,
                source_id=source_id,
                source_url=source_url,
                year=year,
                season=season,
                premiere_date=_extract_after_labels(text, ["首播", "播出", "開播"]),
                platforms=_extract_after_labels(text, ["平台", "播出平台"]),
                staff=_extract_after_labels(text, ["制作", "製作", "制作公司", "動畫製作"]),
                cast=_extract_after_labels(text, ["聲優", "声优", "CAST"]),
                tags=_extract_after_labels(text, ["類型", "类型", "標籤", "标签"]),
                cover_url=cover_url,
            )
        )

    return records


def parse_detail_html(html: str, base_url: str, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
    soup = BeautifulSoup(html, "html.parser")
    page_text = _collapse_whitespace(soup.get_text(" ", strip=True))

    synopsis = _section_text(soup, ["簡介"])
    staff = _section_text(soup, ["製作陣容", "制作阵容"])
    cast = _section_text(soup, ["登場角色 / 演出聲優", "登場角色", "演出聲優", "演出声优"])
    tags = _join_tokens(_section_tokens(soup, ["作品元素", "標籤", "标签"]))
    platforms = _join_tokens(_section_tokens(soup, ["動畫播出平台", "播出平台", "平台"]))
    pv_url = _section_first_link(soup, ["宣傳影片", "宣传影片", "PV"], base_url)
    cover_url = _meta_content(soup, property_name="og:image") or fallback.cover_url

    return AnimeSourceRecord(
        title_cn=_first_non_empty(_meta_content(soup, property_name="og:title"), _headline_text(soup), fallback.title_cn) or fallback.title_cn,
        source_id=_source_id_from_url(source_url) or fallback.source_id,
        source_url=source_url,
        year=fallback.year,
        season=fallback.season,
        title_jp=fallback.title_jp,
        title_en=fallback.title_en,
        aliases=fallback.aliases,
        synopsis=synopsis or fallback.synopsis,
        premiere_date=_extract_date(page_text) or fallback.premiere_date,
        platforms=platforms or fallback.platforms,
        staff=staff or fallback.staff,
        cast=cast or fallback.cast,
        tags=tags or fallback.tags,
        pv_url=pv_url or fallback.pv_url,
        cover_url=urljoin(base_url, cover_url) if cover_url else fallback.cover_url,
    )


def _candidate_blocks(soup: BeautifulSoup):
    selectors = [
        ".anime-list .item",
        ".season-anime .item",
        ".anime-item",
        "article",
        "li",
        "tr",
    ]
    for selector in selectors:
        blocks = soup.select(selector)
        if blocks:
            return blocks
    return soup.select("a[href]")


def _best_link(block):
    links = block.select("a[href]") if hasattr(block, "select") else []
    if not links and getattr(block, "name", None) == "a":
        return block
    detail_links = [link for link in links if "/animes/" in link.get("href", "").lower()]
    return (detail_links or links or [None])[0]


def _title_from_block(block, link) -> str | None:
    title_selectors = [".title", ".anime-title", "h1", "h2", "h3", "h4"]
    for selector in title_selectors:
        node = block.select_one(selector) if hasattr(block, "select_one") else None
        if node:
            title = node.get_text(" ", strip=True)
            if title:
                return title
    if link:
        title = link.get("title") or link.get_text(" ", strip=True)
        if title:
            return title
    text = block.get_text(" ", strip=True)
    return text[:120] if text else None


def _source_id_from_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/").split("/")[-1] or None


def _cover_url_from_block(block, link, base_url: str) -> str | None:
    candidates = []

    if hasattr(link, "select_one"):
        candidates.extend([
            link.select_one("picture source[srcset]"),
            link.select_one("picture img"),
            link.select_one("img"),
        ])

    if hasattr(block, "select_one"):
        candidates.extend([
            block.select_one("picture source[srcset]"),
            block.select_one("picture img"),
            block.select_one("img"),
        ])

    for node in candidates:
        src = _image_source(node)
        if src:
            return urljoin(base_url, src)

    return None


def _image_source(node) -> str | None:
    if node is None:
        return None

    srcset = node.get("srcset")
    if srcset and srcset.strip():
        first = srcset.split(",", 1)[0].strip().split(" ", 1)[0]
        if first:
            return first

    for attr in ("data-src", "data-original", "src"):
        value = node.get(attr)
        if value and value.strip():
            return value.strip()

    return None


def _extract_after_labels(text: str, labels: list[str]) -> str | None:
    for label in labels:
        marker = f"{label}:"
        alt_marker = f"{label}："
        for actual in (marker, alt_marker):
            if actual in text:
                return text.split(actual, 1)[1].split("  ", 1)[0][:255].strip() or None
    return None


def _headline_text(soup: BeautifulSoup) -> str | None:
    for selector in ("h1", "h2", "header h1"):
        node = soup.select_one(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if text:
                return text
    return None


def _section_text(soup: BeautifulSoup, labels: list[str]) -> str | None:
    heading = _find_section_heading(soup, labels)
    if heading is None:
        return None

    parts = [_clean_multiline_text(node.get_text("\n", strip=True)) for node in _section_nodes(heading)]
    value = "\n".join(part for part in parts if part)
    if value:
        return value

    parent = getattr(heading, "parent", None)
    if parent is None:
        return None
    raw = _clean_multiline_text(parent.get_text("\n", strip=True))
    for label in labels:
        if raw.startswith(label):
            raw = raw[len(label) :].strip(" ：:\n")
            break
    return raw or None


def _section_tokens(soup: BeautifulSoup, labels: list[str]) -> list[str]:
    heading = _find_section_heading(soup, labels)
    if heading is None:
        return []

    tokens: list[str] = []
    for node in _section_nodes(heading):
        candidates = []
        if hasattr(node, "select"):
            candidates.extend(node.select("a, li, .tag, .chip, .badge"))
        if not candidates:
            candidates = [node]

        for candidate in candidates:
            text = _collapse_whitespace(candidate.get_text(" ", strip=True))
            text = re.sub(r"\(\d+\)$", "", text).strip()
            if text and text not in tokens:
                tokens.append(text)
    return tokens


def _section_first_link(soup: BeautifulSoup, labels: list[str], base_url: str) -> str | None:
    heading = _find_section_heading(soup, labels)
    if heading is None:
        return None

    links = []
    for node in _section_nodes(heading) or [getattr(heading, "parent", None)]:
        if node is None:
            continue
        if getattr(node, "name", None) == "a" and node.get("href"):
            links.append(node)
            continue
        if hasattr(node, "select"):
            links.extend(node.select("a[href]"))

    preferred = []
    fallback = []
    for link in links:
        href = link.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if any(keyword in absolute.lower() for keyword in ("youtube", "youtu.be", "bilibili", "video")):
            preferred.append(absolute)
        else:
            fallback.append(absolute)
    return (preferred or fallback or [None])[0]


def _extract_date(text: str) -> str | None:
    patterns = [
        r"首映日期[^\d]*(\d{4}-\d{2}-\d{2})",
        r"(?:首播|播出|開播)[^\d]*(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _join_tokens(values: list[str]) -> str | None:
    deduped = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return ", ".join(deduped) if deduped else None
