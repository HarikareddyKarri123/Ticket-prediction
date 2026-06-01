import re
import string

import nltk
from nltk.corpus import stopwords

# Download stopwords once when the module is first imported.
try:
    _STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    _STOP_WORDS = set(stopwords.words("english"))


def preprocess_text(text: str) -> str:
    """
    Clean ticket text for ML models.

    Steps:
    1. Convert to lowercase
    2. Remove punctuation
    3. Remove English stopwords
    """
    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    words = [word for word in words if word not in _STOP_WORDS]
    return " ".join(words)
