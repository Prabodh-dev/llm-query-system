import re
from typing import List, Dict, Iterable

DEFAULT_KEYWORDS = [
    "agreement", "party", "indemnify", "warranty", "liability", "confidential",
    "termination", "governing law", "force majeure", "intellectual property",
    "Section", "Clause", "Policy", "Insurance",
]

def extract_keyword_spans(text: str, keywords: Iterable[str], case_insensitive: bool = True) -> List[Dict[str, object]]:
    flags = re.IGNORECASE if case_insensitive else 0
    spans, seen = [], set()

    for kw in set(keywords):
        pattern = re.compile(rf"\\b{re.escape(kw)}\\b", flags=flags)
        for match in pattern.finditer(text):
            matched_text = match.group(0)
            key = (match.start(), match.end(), matched_text.lower())
            if key in seen: continue
            seen.add(key)
            spans.append({
                "keyword": kw, "start": match.start(), "end": match.end(), "matched_text": matched_text
            })

    spans.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    filtered = []
    for span in spans:
        if not filtered or span["start"] >= filtered[-1]["end"]:
            filtered.append(span)
    return filtered

def build_html_from_spans(text: str, spans: List[Dict[str, object]], tag="mark", extra_attrs="") -> str:
    if not spans: return text
    parts, last_idx = [], 0
    for span in sorted(spans, key=lambda s: s["start"]):
        parts.append(text[last_idx:span["start"]])
        snippet = text[span["start"]:span["end"]]
        open_tag = f"<{tag} {extra_attrs}>".strip() if extra_attrs else f"<{tag}>"
        parts.append(f"{open_tag}{snippet}</{tag}>")
        last_idx = span["end"]
    parts.append(text[last_idx:])
    return "".join(parts)

def build_markdown_from_spans(text: str, spans: List[Dict[str, object]]) -> str:
    if not spans: return text
    parts, last_idx = [], 0
    for span in sorted(spans, key=lambda s: s["start"]):
        parts.append(text[last_idx:span["start"]])
        parts.append(f"**{text[span['start']:span['end']]}**")
        last_idx = span["end"]
    parts.append(text[last_idx:])
    return "".join(parts)

def extract_snippets_from_spans(text: str, spans: List[Dict[str, object]], window: int = 40) -> List[Dict[str, object]]:
    snippets, text_len = [], len(text)
    for span in spans:
        snippet = text[max(0, span["start"] - window):min(text_len, span["end"] + window)].strip()
        snippets.append({
            "keyword": span["keyword"],
            "matched_text": span["matched_text"],
            "snippet": snippet,
            "span_start": span["start"],
            "span_end": span["end"],
        })
    return snippets

def highlight_html(text: str) -> str:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return build_html_from_spans(text, spans)

def highlight_markdown(text: str) -> str:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return build_markdown_from_spans(text, spans)

def extract_snippets(text: str, window: int = 40) -> List[Dict[str, object]]:
    spans = extract_keyword_spans(text, DEFAULT_KEYWORDS)
    return extract_snippets_from_spans(text, spans, window)