import re

# Common deadline phrases found in support tickets.
DEADLINE_PATTERNS = [
    r"\basap\b",
    r"\bby\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bbefore\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bby\s+tomorrow\b",
    r"\bbefore\s+tomorrow\b",
    r"\bby\s+today\b",
    r"\bbefore\s+today\b",
    r"\bby\s+end\s+of\s+(?:day|week|month)\b",
    r"\bbefore\s+end\s+of\s+(?:day|week|month)\b",
    r"\bin\s+\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks)\b",
    r"\bwithin\s+\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks)\b",
    r"\bby\s+\d{1,2}\s*(?:am|pm)\b",
    r"\bbefore\s+\d{1,2}\s*(?:am|pm)\b",
    r"\bby\s+\d{1,2}:\d{2}\s*(?:am|pm)?\b",
    r"\bbefore\s+\d{1,2}:\d{2}\s*(?:am|pm)?\b",
    r"\bby\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
    r"\bbefore\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
    r"\bby\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
    r"\bbefore\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
    r"\bby\s+\d{4}[/-]\d{1,2}[/-]\d{1,2}(?:\s+\d{1,2}:\d{2})?\b",
    r"\bbefore\s+\d{4}[/-]\d{1,2}[/-]\d{1,2}(?:\s+\d{1,2}:\d{2})?\b",
    r"\burgent(?:ly)?\b",
    r"\bbefore\s+\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    r"\bby\s+\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    r"\burgent(?:ly)?\b",
    r"\bimmediately\b",
    r"\bas\s+soon\s+as\s+possible\b",
]

_COMPILED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in DEADLINE_PATTERNS
]


def extract_deadline(text: str):
    """
    Find the first deadline phrase in ticket text.

    Returns the matched phrase or None if nothing is found.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    for pattern in _COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()

    return None
