"""Excel/CSV contact import: column auto-detection, mapped import, and
validation-aware persistence into the contacts table (never silently drops
rows - invalid/duplicate rows are imported flagged, not discarded).
"""
import json
import os
from dataclasses import dataclass, field

import pandas as pd

from app.repositories import contacts_repo
from app.services.validation import validate_contact

_NAME_KEYWORDS = ["name", "full name", "contact name", "customer", "customer name"]
_PHONE_KEYWORDS = ["phone", "mobile", "contact no", "contact number", "number", "mobile number", "phone number"]
_EMAIL_KEYWORDS = ["email", "e-mail", "email address"]


def _normalize_header(h: str) -> str:
    return "".join(ch for ch in str(h).lower().strip() if ch.isalnum() or ch == " ").strip()


def _best_match(headers: list[str], keywords: list[str]) -> str | None:
    best, best_score = None, 0
    for h in headers:
        norm = _normalize_header(h)
        score = 0
        for kw in keywords:
            if norm == kw:
                score = max(score, 100)
            elif kw in norm:
                score = max(score, 50)
        if score > best_score:
            best, best_score = h, score
    return best


def _cell(value) -> str:
    """Normalize a pandas cell (which may be NaN for blanks) to a plain string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def read_excel(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path, dtype=str, keep_default_na=False)
    return pd.read_excel(file_path, engine="openpyxl", dtype=str)


def detect_columns(df: pd.DataFrame) -> dict:
    headers = list(df.columns)
    return {
        "name": _best_match(headers, _NAME_KEYWORDS),
        "phone": _best_match(headers, _PHONE_KEYWORDS),
        "email": _best_match(headers, _EMAIL_KEYWORDS),
    }


@dataclass
class ImportResult:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    rows: list[dict] = field(default_factory=list)  # per-row detail for the Validate step UI


def import_contacts(
    file_path: str, df: pd.DataFrame, name_col: str, phone_col: str, email_col: str | None = None
) -> ImportResult:
    result = ImportResult()
    seen_phones: dict[str, int] = {}  # phone_e164 -> row index of canonical (first) occurrence
    source_file = os.path.basename(file_path)

    for idx, row in df.iterrows():
        result.total += 1
        name = _cell(row.get(name_col))
        phone_raw = _cell(row.get(phone_col))
        email = _cell(row.get(email_col)) if email_col else None
        extra = {k: v for k, v in row.items() if k not in (name_col, phone_col, email_col)}

        is_valid, phone_e164, error = validate_contact(name, phone_raw)

        if is_valid:
            if phone_e164 in seen_phones:
                is_valid = False
                error = f"Duplicate of row {seen_phones[phone_e164] + 2}"  # +2: header row + 1-index
            else:
                existing = contacts_repo.find_by_phone_e164(phone_e164)
                if existing is not None:
                    is_valid = False
                    error = "Already exists in contacts"
                else:
                    seen_phones[phone_e164] = idx

        contact_id = contacts_repo.create(
            name=name,
            phone_raw=phone_raw,
            phone_e164=phone_e164 or "",
            email=email or None,
            extra_json=json.dumps(extra, default=str) if extra else None,
            source_file=source_file,
            is_valid=is_valid,
            validation_error=error,
        )

        if is_valid:
            result.valid += 1
        elif error and error.startswith("Duplicate") or error == "Already exists in contacts":
            result.duplicates += 1
        else:
            result.invalid += 1

        result.rows.append(
            {"contact_id": contact_id, "row": idx + 2, "name": name, "phone": phone_raw, "is_valid": is_valid, "error": error}
        )

    return result
