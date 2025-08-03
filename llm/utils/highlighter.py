import re
from typing import List, Dict, Iterable

# Default legal-ish keywords; you can extend or replace when calling functions, chat gpt idhan kuduthan

DEFAULT_KEYWORDS = [
    "agreement",
    "party",
    "indemnify",
    "warranty",
    "liability",
    "confidential",
    "termination",
    "governing law",
    "force majeure",
    "intellectual property",
    "Section", 
    "Clause",
    "Policy",
    "Insurance",
]


def extract_keyword_spans(
    text: str,
    keywords: Iterable[str],
    case_insensitive: bool = True,
) -> List[Dict[str, object]]:
    """
    Finds all whole-word occurrences of keywords in the text and returns structured spans.
    Handles deduplication and is case-insensitive by defaultt.

    Returns list of dicts with:
      - keyword: the original keyword from the list
      - start: start index in text
      - end: end index in text
      - matched_text: the actual substring matched
    """
    flags = re.IGNORECASE if case_insensitive else 0
    spans = []
    seen = set()

    for kw in set(keywords):
        pattern = re.compile(rf"\b{re.escape(kw)}\b", flags=flags)
        for match in pattern.finditer(text):

            #avoiding duplicates ( dupe dupe dupe )
            matched_text = match.group(0)
            key = (match.start(), match.end(), matched_text.lower() if case_insensitive else matched_text)
            if key in seen:
                continue
            seen.add(key)
            spans.append({
                "keyword": kw,
                "start": match.start(),
                "end": match.end(),
                "matched_text": matched_text,
            })

    # Sort spans by start index

    spans.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))

    # Remove nested/contained spans: keep the longer one  if its overlapping

    filtered = []
    for span in spans:
        if not filtered:
            filtered.append(span)
            continue
        last = filtered[-1]

        # If current span is fully inside previous kept span then skip it polease

        if span["start"] >= last["start"] and span["end"] <= last["end"]:
            continue
        filtered.append(span)
    return filtered


def build_html_from_spans(
    text: str,
    spans: List[Dict[str, object]],
    tag: str = "mark",
    extra_attrs: str = "",
) -> str:
    """
    Builds an HTML-highlighted ( it looks prettier ) version of the text by wrapping spans in <tag>.
    Non-overlapping is assumed after extract_keyword_spans filtering.

    Args:
        text: Original text.
        spans: List of spans (should be sorted and filtered).
        tag: HTML tag to wrap around matches (default: <mark>).
        extra_attrs: Additional attributes inside opening tag (e.g., 'class="kw"').

    Returns:
        HTML string with highlights.
    """
    if not spans:
        return text

    parts = []
    last_idx = 0
    for span in sorted(spans, key=lambda s: s["start"]):
        start, end = span["start"], span["end"]
        # Append segment before this keyword
        parts.append(text[last_idx:start])
        snippet = text[start:end]
        open_tag = f"<{tag} {extra_attrs}>".strip()
        if extra_attrs == "":
            open_tag = f"<{tag}>"
        parts.append(f"{open_tag}{snippet}</{tag}>")
        last_idx = end
    parts.append(text[last_idx:])
    return "".join(parts)


def build_markdown_from_spans(
    text: str,
    spans: List[Dict[str, object]],
) -> str:
    """
    Builds a Markdown-highlighted ( bold ig ) version of the text by bolding keyword spans.
    """
    if not spans:
        return text

    parts = []
    last_idx = 0
    for span in sorted(spans, key=lambda s: s["start"]):
        start, end = span["start"], span["end"]
        parts.append(text[last_idx:start])
        snippet = text[start:end]
        parts.append(f"**{snippet}**")
        last_idx = end
    parts.append(text[last_idx:])
    return "".join(parts)


def extract_snippets_from_spans(
    text: str,
    spans: List[Dict[str, object]],
    window: int = 40,
) -> List[Dict[str, object]]:
    """
    For each span, extract a contextual snippet around it of +/- window characters.
    Returns a list of dicts with 'keyword', 'snippet', 'start', 'end'.
    """
    snippets = []
    text_len = len(text)
    for span in spans:
        start, end = span["start"], span["end"]
        snippet_start = max(0, start - window)
        snippet_end = min(text_len, end + window)
        snippet = text[snippet_start:snippet_end].strip()
        snippets.append({
            "keyword": span["keyword"],
            "matched_text": span["matched_text"],
            "snippet": snippet,
            "span_start": start,
            "span_end": end,
        })
    return snippets


# Optional convenience wrappers using the default keywords
def highlight_html(text: str) -> str:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return build_html_from_spans(text, spans)


def highlight_markdown(text: str) -> str:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return build_markdown_from_spans(text, spans)


def extract_snippets(text: str, window: int = 40) -> List[Dict[str, object]]:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return extract_snippets_from_spans(text, spans, window=window)


# testing if this works ( please work!! ill cry )
if __name__ == "__main__":
    sample = (
        "This agreement includes a termination clause. "
        "The governing law doesn't support the confidential insurance policies, kindly refer to Section 1 A and clause 499032."
    )
    kws = ["agreement", "termination", "governing law", "confidential", "insurance", "clause", "section"]
    spans = extract_keyword_spans(sample, kws)
    print("Spans:", spans)

    html = build_html_from_spans(sample, spans, tag="mark", extra_attrs='class="kw"')
    print("\nHTML Highlighted:\n", html)

    md = build_markdown_from_spans(sample, spans)
    print("\nMarkdown Highlighted:\n", md)

    snippets = extract_snippets_from_spans(sample, spans, window=30)
    print("\nContext Snippets:")
    for s in snippets:
        print(f"- {s['keyword']}: ...{s['snippet']}...")
