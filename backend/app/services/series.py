import re
import string
import unicodedata
from dataclasses import dataclass


_OPEN_BRACKETS = "（(【["
_CLOSE_BRACKETS = "）)】]"
_CHINESE_NUMERALS = "一二三四五六七八九十百"
_CJK_ARC_CHARS = r"\u4e00-\u9fff·"
_ROMAN_NUMERALS = "XIII|XII|XI|IX|VIII|VII|VI|IV|III|II"
_SEPARATOR_PUNCTUATION = re.escape(
    string.punctuation + "·：！？，。、；…（）《》「」『』【】―—–"
)

# 剥离后缀后，剩余标题结尾需要清理的悬挂标点（含全/半角）。
_HANGING_PUNCTUATION = "·-―—–:：!！?？~～,，、.。;；" + _CLOSE_BRACKETS + "”』」"


@dataclass(frozen=True)
class SeriesInfo:
    series_key: str
    series_title: str
    season_label: str | None = None


# 归一化算法版本：规则变更时递增，启动迁移将据此对存量数据全量重算。
SERIES_ALGORITHM_VERSION = 3


_RULE_CHINESE_SEASON_NUMERAL = rf"(?:[0-9]+|[{_CHINESE_NUMERALS}]+)"
_RULE_CHINESE_SEASON_BODY = rf"第{_RULE_CHINESE_SEASON_NUMERAL}[季期部章]度?"

# 数据源站点会在标题结尾附加签名（如 " | YourAnimes"），剥离季度后缀前先清理。
_SOURCE_SIGNATURE = re.compile(r"\s*[|｜]\s*youranimes\s*$", re.IGNORECASE)

# 规则按顺序尝试，命中即停。
_RULES: tuple[tuple[re.Pattern[str], str, int], ...] = (
    # 1. 第X季/期/部/章/季度（X 为阿拉伯数字或中文数字，可被全/半角括号包裹）。
    (
        re.compile(
            rf"(?:[{re.escape(_OPEN_BRACKETS)}]{_RULE_CHINESE_SEASON_BODY}[{re.escape(_CLOSE_BRACKETS)}]"
            rf"|{_RULE_CHINESE_SEASON_BODY})$"
        ),
        "chinese_season",
        1,
    ),
    # 2. XX篇（1-8 个中文字符（含·）+ 篇，前面必须有空白或左括号分隔）。
    (
        re.compile(
            rf"[\s{re.escape(_OPEN_BRACKETS)}][{_CJK_ARC_CHARS}]{{1,8}}篇[{re.escape(_CLOSE_BRACKETS)}]?$"
        ),
        "arc",
        1,
    ),
    # 3. 分割放送（split-cour）标记：前半/後半（可带“部”）、前/後編（篇）、上/下編（篇/巻）、Part N。
    (
        re.compile(
            rf"[\s{re.escape(_OPEN_BRACKETS)}]((?:[前後]半部?|[前後][編篇]|[上下][編篇巻]|part\s*\d{{1,2}})"
            rf"[{re.escape(_CLOSE_BRACKETS)}]?)$",
            re.IGNORECASE,
        ),
        "split_part",
        2,
    ),
    # 4. Season N / Nth Season / Series N（大小写不敏感；必须带数字，
    #    避免 "BEASTARS FINAL SEASON" 这类标题词被误剥）。
    (
        re.compile(
            r"\s+(\d{1,2}(?:st|nd|rd|th)\s+(?:season|series)|(?:season|series)\s+\d{1,2})$",
            re.IGNORECASE,
        ),
        "stripped",
        1,
    ),
    # 5. SN（如 S2，前面须有空白或标点分隔）。
    (re.compile(rf"[\s{_SEPARATOR_PUNCTUATION}](S\d+)$"), "prefixed", 1),
    # 6. 结尾独立罗马数字（大写，前面必须有空白）。
    (re.compile(rf"\s+({_ROMAN_NUMERALS})$"), "stripped", 1),
    # 7. 空白 + 结尾阿拉伯数字（1-2 位，剥离后剩余长度必须 ≥ 2 字符）。
    (re.compile(r"\s+(\d{1,2})$"), "stripped", 2),
)


def extract_series_info(title: str) -> SeriesInfo:
    if not title or not title.strip():
        return SeriesInfo(series_key="", series_title="", season_label=None)

    base = _SOURCE_SIGNATURE.sub("", title.rstrip()).rstrip()
    # 循环剥离以支持组合后缀（如 "4th season 喪失篇"），每轮命中一条规则即停，
    # 最多 3 轮；某轮剥离后为空则回退到该轮之前的标题。
    labels: list[str] = []
    current = base
    for _ in range(3):
        matched = False
        for pattern, kind, min_length in _RULES:
            match = pattern.search(current)
            if match is None:
                continue

            series_title = _clean_remainder(current[: match.start()])
            if len(series_title) < max(min_length, 1):
                continue

            labels.append(_season_label(kind, match))
            current = series_title
            matched = True
            break
        if not matched:
            break

    return SeriesInfo(
        series_key=_normalize_series_key(current),
        series_title=current,
        season_label=" ".join(labels) or None,
    )


def _season_label(kind: str, match: re.Match[str]) -> str:
    suffix = match.group(0)
    if kind == "chinese_season":
        if suffix[0] in _OPEN_BRACKETS and suffix[-1] in _CLOSE_BRACKETS:
            return suffix[1:-1]
        return suffix
    if kind in ("arc", "split_part"):
        label = suffix[1:]
        return label[:-1] if label and label[-1] in _CLOSE_BRACKETS else label
    if kind == "prefixed":
        return suffix[1:]
    return suffix.strip()


def _clean_remainder(remainder: str) -> str:
    cleaned = remainder.rstrip()
    while cleaned and cleaned[-1] in _HANGING_PUNCTUATION:
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def _normalize_series_key(series_title: str) -> str:
    if not series_title:
        return ""

    normalized = unicodedata.normalize("NFKC", series_title).lower()
    normalized = "".join(char for char in normalized if not char.isspace())

    start, end = 0, len(normalized)
    # 两端剥离标点（P）与符号（S，含 NFKC 后的 ~ 等）：
    # 否则无后缀标题 "XX～" 与剥离后缀标题 "XX" 会因尾部波浪号分裂成两个系列。
    while start < end and unicodedata.category(normalized[start])[0] in ("P", "S"):
        start += 1
    while end > start and unicodedata.category(normalized[end - 1])[0] in ("P", "S"):
        end -= 1
    return normalized[start:end]
