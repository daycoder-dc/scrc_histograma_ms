from unicodedata import normalize
import re

def text(text:str):
    normalize_text = text.strip().lower()
    normalize_text = re.sub(r"[^a-z0-9]+", " ", normalize_text)
    normalize_text = normalize_text.strip().replace(" ", "_")
    normalize_text = normalize("NFD", normalize_text)
    return re.sub(r"[\u0300-\u036f]", "", normalize_text)
