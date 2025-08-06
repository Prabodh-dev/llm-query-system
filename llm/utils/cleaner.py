import re
import string
import unicodedata

def clean_text(text: str, lowercase=True, remove_non_ascii=True, remove_punctuation=True, collapse_whitespace=True) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    if lowercase:
        text = text.lower()
    if remove_non_ascii:
        text = text.encode("ascii", errors="ignore").decode("ascii")
    if remove_punctuation:
        translator = str.maketrans("", "", string.punctuation)
        text = text.translate(translator)
    if collapse_whitespace:
        text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_control_chars(text: str) -> str:
    return "".join(ch for ch in text if ch.isprintable() or ch.isspace())