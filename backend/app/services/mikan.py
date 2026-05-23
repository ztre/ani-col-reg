import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.cover_cache import is_known_placeholder_cover_url
from app.services.html_parsing import (
    clean_multiline_text as _clean_multiline_text,
    collapse_whitespace as _collapse_whitespace,
    find_section_heading as _find_section_heading,
    first_non_empty as _first_non_empty,
    meta_content as _meta_content,
    section_nodes as _section_nodes,
)
from app.services.scraper import AnimeSourceRecord, normalize_title


MIKAN_SEASON = {1: "冬", 2: "春", 3: "夏", 4: "秋"}
BANGUMI_SUBJECT_RE = re.compile(r"https?://(?:bgm|bangumi|chii)\.tv/subject/\d+")


@dataclass
class MikanCover:
    title: str
    cover_url: str


class MikanCoverClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_covers(self, year: int, season: int) -> dict[str, str]:
        season_str = MIKAN_SEASON[season]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            html = await _fetch_cover_flow_html(client, self.base_url, year, season_str)
        return {
            normalize_title(cover.title): cover.cover_url
            for cover in parse_mikan_cover_html(html, self.base_url)
        }


class MikanScraper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_season(self, year: int, season: int) -> list[AnimeSourceRecord]:
        season_str = MIKAN_SEASON[season]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            html = await _fetch_cover_flow_html(client, self.base_url, year, season_str)
        return parse_mikan_season_html(html, self.base_url, year, season)

    async def fetch_detail(self, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord | None:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            html = response.text
            detail = parse_mikan_detail_html(html, self.base_url, source_url, fallback=fallback)
            bangumi_url = extract_bangumi_subject_url(html)
            if bangumi_url:
                try:
                    bangumi_response = await client.get(
                        bangumi_url,
                        headers={"Referer": source_url, "User-Agent": "Mozilla/5.0"},
                    )
                    bangumi_response.raise_for_status()
                except Exception:
                    return detail

                bangumi_detail = parse_bangumi_detail_html(
                    bangumi_response.text,
                    bangumi_url,
                    fallback=detail,
                )
                return merge_detail_records(detail, bangumi_detail)
        return detail


async def _fetch_cover_flow_html(client: httpx.AsyncClient, base_url: str, year: int, season_str: str) -> str:
    url = f"{base_url}/Home/BangumiCoverFlowByDayOfWeek"
    response = await client.get(
        url,
        params={"year": year, "seasonStr": season_str},
        headers={
            "Referer": f"{base_url}/",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    response.raise_for_status()
    return _response_html(response)


def _response_html(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "json" not in content_type:
        return response.text

    payload = response.json()
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("html", "data", "content", "result"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
    return response.text


def parse_mikan_cover_html(html: str, base_url: str) -> list[MikanCover]:
    soup = BeautifulSoup(html, "html.parser")
    covers: list[MikanCover] = []
    seen: set[str] = set()

    for image in soup.select("img"):
        src = image.get("data-src") or image.get("data-original") or image.get("src")
        if not src:
            continue

        title = _image_title(image)
        if not title:
            title = _nearby_title(image)
        if not title:
            continue

        url = urljoin(base_url, src)
        key = normalize_title(title)
        if key in seen:
            continue
        seen.add(key)
        covers.append(MikanCover(title=title, cover_url=url))

    return covers


def parse_mikan_season_html(html: str, base_url: str, year: int, season: int) -> list[AnimeSourceRecord]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[AnimeSourceRecord] = []
    seen: set[str] = set()

    items = soup.select("li") or soup.select("a[href*='/Home/Bangumi/']")

    for item in items:
        anchor = item.select_one("a[href*='/Home/Bangumi/']") if hasattr(item, "select_one") else None
        if anchor is None and getattr(item, "name", None) == "a":
            anchor = item
        if anchor is None:
            continue

        source_url = urljoin(base_url, anchor.get("href", ""))
        if not source_url or source_url in seen:
            continue

        image = None
        if hasattr(item, "select_one"):
            image = item.select_one("img, span[data-src], span[data-original], span[src]")
        if image is None and hasattr(anchor, "select_one"):
            image = anchor.select_one("img")

        title = anchor.get("title") or _image_title(image) or _nearby_title(anchor) or anchor.get_text(" ", strip=True)
        if not title:
            continue

        seen.add(source_url)
        records.append(
            AnimeSourceRecord(
                title_cn=title.strip(),
                source_id=_mikan_source_id(source_url),
                source_url=source_url,
                year=year,
                season=season,
                cover_url=urljoin(base_url, _image_source(image)) if _image_source(image) else None,
            )
        )

    return records


def parse_mikan_detail_html(html: str, base_url: str, source_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
    soup = BeautifulSoup(html, "html.parser")
    text = _collapse_whitespace(soup.get_text(" ", strip=True))
    info = _mikan_info_map(soup)
    synopsis = _mikan_overview_text(soup)
    cover_url = _first_valid_mikan_cover_url(
        base_url,
        _mikan_cover_url(soup, base_url),
        _meta_content(soup, property_name="og:image"),
        _first_image(soup),
    )

    return AnimeSourceRecord(
        title_cn=_first_non_empty(_mikan_title(soup), _headline_text(soup), fallback.title_cn) or fallback.title_cn,
        source_id=_mikan_source_id(source_url) or fallback.source_id,
        source_url=source_url,
        year=fallback.year,
        season=fallback.season,
        title_jp=fallback.title_jp,
        title_en=fallback.title_en,
        aliases=fallback.aliases,
        synopsis=synopsis or fallback.synopsis,
        premiere_date=info.get("放送开始") or _extract_mikan_date(text) or fallback.premiere_date,
        platforms=fallback.platforms,
        staff=fallback.staff,
        cast=fallback.cast,
        tags=fallback.tags,
        pv_url=fallback.pv_url,
        cover_url=cover_url or fallback.cover_url,
    )


def parse_bangumi_detail_html(html: str, bangumi_url: str, *, fallback: AnimeSourceRecord) -> AnimeSourceRecord:
    soup = BeautifulSoup(html, "html.parser")
    infobox = _bangumi_infobox(soup)
    tags = _bangumi_tags(soup)
    staff = _bangumi_staff(infobox)
    cast = _bangumi_cast(soup)
    title_jp = _bangumi_title(soup)
    cover_url = _bangumi_cover_url(soup, bangumi_url)

    return AnimeSourceRecord(
        title_cn=infobox.get("中文名") or fallback.title_cn,
        source_id=fallback.source_id,
        source_url=fallback.source_url,
        year=fallback.year,
        season=fallback.season,
        title_jp=title_jp or fallback.title_jp,
        title_en=fallback.title_en,
        aliases=infobox.get("别名") or infobox.get("別名") or fallback.aliases,
        synopsis=_bangumi_synopsis(soup) or fallback.synopsis,
        premiere_date=_normalize_bangumi_date(infobox.get("放送开始")) or fallback.premiere_date,
        platforms=_bangumi_platform(tags) or fallback.platforms,
        staff=staff or fallback.staff,
        cast=cast or fallback.cast,
        tags=", ".join(tags[:12]) or fallback.tags,
        pv_url=fallback.pv_url,
        cover_url=cover_url or fallback.cover_url,
    )


def merge_detail_records(primary: AnimeSourceRecord, supplement: AnimeSourceRecord) -> AnimeSourceRecord:
    return AnimeSourceRecord(
        title_cn=primary.title_cn or supplement.title_cn,
        source_id=primary.source_id or supplement.source_id,
        source_url=primary.source_url or supplement.source_url,
        year=primary.year,
        season=primary.season,
        title_jp=primary.title_jp or supplement.title_jp,
        title_en=primary.title_en or supplement.title_en,
        aliases=primary.aliases or supplement.aliases,
        synopsis=primary.synopsis or supplement.synopsis,
        premiere_date=primary.premiere_date or supplement.premiere_date,
        platforms=primary.platforms or supplement.platforms,
        staff=primary.staff or supplement.staff,
        cast=primary.cast or supplement.cast,
        tags=primary.tags or supplement.tags,
        pv_url=primary.pv_url or supplement.pv_url,
        cover_url=_merge_cover_urls(primary.cover_url, supplement.cover_url),
    )


def extract_bangumi_subject_url(html: str) -> str | None:
    match = BANGUMI_SUBJECT_RE.search(html)
    if not match:
        return None
    return match.group(0)


def _mikan_title(soup: BeautifulSoup) -> str | None:
    node = soup.select_one(".bangumi-title")
    if node is None:
        return None
    text = node.get_text(" ", strip=True)
    return text or None


def _mikan_info_map(soup: BeautifulSoup) -> dict[str, str]:
    info: dict[str, str] = {}
    for node in soup.select(".bangumi-info"):
        text = _collapse_whitespace(node.get_text(" ", strip=True))
        if not text or not re.search(r"[:：]", text):
            continue
        label, value = re.split(r"[:：]", text, maxsplit=1)
        label = label.strip()
        value = value.strip()
        if label and value:
            info[label] = value
    return info


def _mikan_overview_text(soup: BeautifulSoup) -> str | None:
    content = _header2_section_text(soup, ["概况介绍", "概況介紹", "简介", "簡介"])
    if not content:
        return None
    cleaned = content.split("[简介原文]", 1)[0].strip()
    return cleaned or content


def _header2_section_text(soup: BeautifulSoup, labels: list[str]) -> str | None:
    label_set = {_collapse_whitespace(label) for label in labels}
    for header in soup.select(".header2"):
        text = _collapse_whitespace(header.get_text(" ", strip=True))
        if text not in label_set:
            continue

        content: list[str] = []
        for sibling in header.next_siblings:
            classes = getattr(sibling, "get", lambda *_: [])("class", []) if hasattr(sibling, "get") else []
            if "header2" in classes:
                break
            if not hasattr(sibling, "get_text"):
                continue
            section_text = _clean_multiline_text(sibling.get_text("\n", strip=True))
            if section_text:
                content.append(section_text)

        if content:
            return "\n".join(content)
    return None


def _mikan_cover_url(soup: BeautifulSoup, base_url: str) -> str | None:
    poster = soup.select_one(".bangumi-poster")
    if poster is not None:
        style = poster.get("style") or ""
        match = re.search(r"background-image\s*:\s*url\((['\"]?)([^)]+?)\1\)", style, flags=re.I)
        if match:
            return urljoin(base_url, match.group(2).strip())

        image = poster.select_one("img")
        src = _image_source(image)
        if src:
            return urljoin(base_url, src)

    image = soup.select_one("img")
    src = _image_source(image)
    if not src:
        return None
    return urljoin(base_url, src)


def _first_valid_mikan_cover_url(base_url: str, *candidates: str | None) -> str | None:
    for candidate in candidates:
        if not candidate:
            continue
        resolved = urljoin(base_url, candidate)
        if is_known_placeholder_cover_url(resolved):
            continue
        return resolved
    return None


def _merge_cover_urls(primary_cover_url: str | None, supplement_cover_url: str | None) -> str | None:
    if primary_cover_url and not is_known_placeholder_cover_url(primary_cover_url):
        return primary_cover_url
    return supplement_cover_url or primary_cover_url


def _bangumi_title(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("#headerSubject .nameSingle") or soup.select_one("#headerSubject a")
    if node is None:
        return None
    text = node.get_text(" ", strip=True)
    return text or None


def _bangumi_synopsis(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("#subject_summary")
    if node is None:
        return None
    text = _clean_multiline_text(node.get_text("\n", strip=True))
    return text or None


def _bangumi_infobox(soup: BeautifulSoup) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in soup.select("#infobox li"):
        label_node = row.select_one(".tip")
        if label_node is None:
            continue
        label = _collapse_whitespace(label_node.get_text(" ", strip=True)).strip(" ：:")
        text = _collapse_whitespace(row.get_text(" ", strip=True))
        if not text.startswith(label):
            continue
        value = text[len(label) :].strip(" ：:")
        if label and value:
            result[label] = value
    return result


def _bangumi_tags(soup: BeautifulSoup) -> list[str]:
    tags: list[str] = []
    for node in soup.select(".subject_tag_section .inner a"):
        text = _collapse_whitespace(node.get_text(" ", strip=True))
        text = re.sub(r"\s+\d+$", "", text).strip()
        if text and text not in tags:
            tags.append(text)
    return tags


def _bangumi_staff(infobox: dict[str, str]) -> str | None:
    labels = ["动画制作", "制作公司", "导演", "脚本", "系列构成", "人物设定", "原作", "音乐"]
    parts = [f"{label}: {infobox[label]}" for label in labels if infobox.get(label)]
    return "；".join(parts[:8]) or None


def _bangumi_cast(soup: BeautifulSoup) -> str | None:
    cast: list[str] = []
    for node in soup.select("#browserItemList .item"):
        text = _collapse_whitespace(node.get_text(" ", strip=True))
        text = re.sub(r"\s*\(\+\d+\)", "", text).strip()
        if text:
            cast.append(text)
    return "；".join(cast[:10]) or None


def _bangumi_platform(tags: list[str]) -> str | None:
    for tag in tags:
        if tag.upper() in {"TV", "WEB", "OVA", "OAD"}:
            return tag.upper()
        if tag in {"剧场版", "電影", "电影"}:
            return tag
    return None


def _bangumi_cover_url(soup: BeautifulSoup, bangumi_url: str) -> str | None:
    image = soup.select_one("#bangumiInfo .cover img") or soup.select_one(".subjectCover img")
    src = _image_source(image)
    if not src:
        return None
    return urljoin(bangumi_url, src)


def _normalize_bangumi_date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _image_title(image) -> str | None:
    for attr in ("alt", "title"):
        value = image.get(attr)
        if value and value.strip():
            return value.strip()
    return None


def _nearby_title(image) -> str | None:
    parent = image.find_parent(["a", "div", "li", "article"])
    if parent is None:
        return None

    selectors = [".an-text", ".title", ".bangumi-title", "h3", "h4", "a"]
    for selector in selectors:
        node = parent.select_one(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if text:
                return text

    text = parent.get_text(" ", strip=True)
    return text[:120] if text else None


def _mikan_source_id(source_url: str | None) -> str | None:
    if not source_url:
        return None
    return source_url.rstrip("/").split("/")[-1] or None


def _image_source(image) -> str | None:
    if image is None:
        return None
    for attr in ("data-src", "data-original", "src"):
        value = image.get(attr)
        if value and value.strip():
            return value.strip()
    return None


def _headline_text(soup: BeautifulSoup) -> str | None:
    for selector in ("h1", "h2", ".bangumi-title", ".bangumi-name"):
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

    content = "\n".join(
        _clean_multiline_text(node.get_text("\n", strip=True))
        for node in _section_nodes(heading)
        if _clean_multiline_text(node.get_text("\n", strip=True))
    )
    if content:
        return content

    parent = getattr(heading, "parent", None)
    if parent is None:
        return None
    raw = _clean_multiline_text(parent.get_text("\n", strip=True))
    for label in labels:
        if raw.startswith(label):
            raw = raw[len(label) :].strip(" ：:\n")
            break
    return raw or None


def _first_image(soup: BeautifulSoup) -> str | None:
    for image in soup.select("img"):
        src = _image_source(image)
        if src:
            return src
    return None


def _extract_mikan_date(text: str) -> str | None:
    match = re.search(r"放送开始[:：]\s*([0-9./-]+)", text)
    if match:
        return match.group(1)
    return None
