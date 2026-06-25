import re


STOPWORDS = {
    "a", "al", "and", "con", "de", "del", "el", "en", "for", "la", "las",
    "los", "of", "para", "por", "the", "to", "un", "una", "y", "or", "o",
}


def words(text):
    return {
        word
        for word in re.findall(r"[a-z0-9+#.]+", (text or "").lower())
        if len(word) > 2 and word not in STOPWORDS
    }


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value):
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"
