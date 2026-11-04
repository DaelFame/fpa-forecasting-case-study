from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, datetime
from typing import Any


_QUARTER_RE = re.compile(r"(?:^|\b)(?:q|trim(?:estre)?\s*)([1-4])\b", re.IGNORECASE)
_QUARTER_WORD_RE = re.compile(r"([1-4])\s*(?:er|do|ro|to|º|ª)?\s*trim(?:estre)?", re.IGNORECASE)


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def clean_display_label(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("▲", " ").replace("▼", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_label(value: Any) -> str:
    text = strip_accents(clean_display_label(value)).casefold()
    text = text.replace("%", " pct ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_year_value(value: Any, min_year: int = 2000, max_year: int = 2100) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return False
        if float(value).is_integer():
            year = int(value)
            return min_year <= year <= max_year
        return False
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"\d{4}(?:\.0+)?", text):
            year = int(float(text))
            return min_year <= year <= max_year
    return False


def year_from_value(value: Any) -> int | None:
    if not is_year_value(value):
        return None
    if isinstance(value, str):
        return int(float(value.strip()))
    return int(value)


def quarter_from_label(value: Any) -> int | None:
    if value is None:
        return None
    text = strip_accents(str(value)).casefold()
    match = _QUARTER_WORD_RE.search(text)
    if match:
        return int(match.group(1))
    match = _QUARTER_RE.search(text)
    if match:
        return int(match.group(1))
    return None


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def value_type(value: Any) -> str:
    if value is None:
        return "empty"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, (datetime, date)):
        return "date"
    return "string"


def value_as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, str):
        text = value.strip().replace(".", "").replace(",", ".")
        try:
            number = float(text)
        except ValueError:
            return None
        return number if math.isfinite(number) else None
    return None


def format_number(value: float | int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def period_string(year: int, quarter: int | None = None) -> str:
    if quarter is None:
        return str(year)
    return f"{year}-Q{quarter}"


def period_sort_key(period: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})(?:-Q([1-4]))?", period or "")
    if not match:
        return (9999, 9)
    return (int(match.group(1)), int(match.group(2) or 0))

