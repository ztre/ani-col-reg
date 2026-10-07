from bs4 import BeautifulSoup


def clean_multiline_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def meta_content(soup: BeautifulSoup, *, property_name: str | None = None, name: str | None = None) -> str | None:
    attrs = {}
    if property_name:
        attrs["property"] = property_name
    if name:
        attrs["name"] = name
    node = soup.find("meta", attrs=attrs)
    if node is None:
        return None
    content = node.get("content")
    return content.strip() if content and content.strip() else None


_HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "strong", "dt", "summary", "p", "span", "div"]


def find_section_heading(soup: BeautifulSoup, labels: list[str]):
    label_set = {collapse_whitespace(label) for label in labels}

    # 第一轮：文本恰好等于标签词（精确命中，优先返回语义最贴近的标题节点）。
    # 注意：包裹“标题+内容”的容器 div 在文档序上先于内部 h2 被遍历，
    # 精确匹配可避免误把整个内容区块当作标题。
    for tag in soup.find_all(_HEADING_TAGS):
        text = collapse_whitespace(tag.get_text(" ", strip=True))
        if text and text in label_set:
            return tag

    # 第二轮：前缀匹配，但候选文本必须足够短（防止吞并内容区）。
    for tag in soup.find_all(_HEADING_TAGS):
        text = collapse_whitespace(tag.get_text(" ", strip=True))
        if text and len(text) <= 6 and any(text.startswith(label) for label in label_set):
            return tag
    return None


def section_nodes(heading) -> list:
    nodes = []
    for sibling in heading.next_siblings:
        if getattr(sibling, "name", None) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            break
        if hasattr(sibling, "get_text"):
            nodes.append(sibling)

    if nodes:
        return nodes

    parent = getattr(heading, "parent", None)
    if parent is None:
        return []

    seen_heading = False
    for child in parent.children:
        if child is heading:
            seen_heading = True
            continue
        if not seen_heading:
            continue
        if getattr(child, "name", None) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            break
        if hasattr(child, "get_text"):
            nodes.append(child)
    return nodes