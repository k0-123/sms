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
    headers = [str(c) for c in df.columns]
    name = _best_match(headers, _NAME_KEYWORDS)
    phone = _best_match(headers, _PHONE_KEYWORDS)
    email = _best_match(headers, _EMAIL_KEYWORDS)

    # If phone is not matched by keywords, test column values for phone-like content
    if not phone and len(headers) > 0:
        import re
        for col in df.columns:
            if str(col) == name or str(col) == email:
                continue
            sample_vals = df[col].dropna().head(5)
            numeric_count = sum(
                1 for v in sample_vals
                if re.sub(r"[^\d]", "", str(v)).isdigit() and len(re.sub(r"[^\d]", "", str(v))) >= 8
            )
            if numeric_count > 0:
                phone = str(col)
                break
        # Fallback to single column if only 1 column is present
        if not phone and len(headers) == 1:
            phone = headers[0]
            if name == phone:
                name = None

    return {
        "name": name,
        "phone": phone,
        "email": email,
    }


@dataclass
class ImportResult:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    rows: list[dict] = field(default_factory=list)  # per-row detail for the Validate step UI


def import_contacts(
    *args,
    file_path: str | None = None,
    df: pd.DataFrame | None = None,
    name_col: str | None = None,
    phone_col: str | None = None,
    email_col: str | None = None,
    column_mapping: dict | None = None,
    source_file: str | None = None,
    **kwargs,
) -> ImportResult:
    """Imports contacts from a pandas DataFrame or file path.

    Supports multiple calling conventions:
      - import_contacts(file_path, df, name_col, phone_col, email_col=None)
      - import_contacts(df, column_mapping, source_file=path)
      - import_contacts(df, name_col=..., phone_col=..., source_file=...)
      - import_contacts(file_path=path, df=df, ...)
    """
    # Parse positional arguments
    if len(args) >= 1:
        if isinstance(args[0], pd.DataFrame):
            df = args[0]
            if len(args) >= 2:
                if isinstance(args[1], dict):
                    column_mapping = args[1]
                elif isinstance(args[1], (str, type(None))):
                    name_col = args[1]
                    if len(args) >= 3 and isinstance(args[2], (str, type(None))):
                        phone_col = args[2]
                    if len(args) >= 4 and isinstance(args[3], (str, type(None))):
                        email_col = args[3]
        elif isinstance(args[0], str):
            file_path = args[0]
            if len(args) >= 2 and isinstance(args[1], pd.DataFrame):
                df = args[1]
                if len(args) >= 3:
                    if isinstance(args[2], dict):
                        column_mapping = args[2]
                    elif isinstance(args[2], (str, type(None))):
                        name_col = args[2]
                        if len(args) >= 4 and isinstance(args[3], (str, type(None))):
                            phone_col = args[3]
                        if len(args) >= 5 and isinstance(args[4], (str, type(None))):
                            email_col = args[4]

    if column_mapping:
        if name_col is None:
            name_col = column_mapping.get("name")
        if phone_col is None:
            phone_col = column_mapping.get("phone")
        if email_col is None:
            email_col = column_mapping.get("email")

    resolved_source_file = source_file or file_path or kwargs.get("source_path") or "contacts_file"
    source_filename = os.path.basename(resolved_source_file)

    if df is None:
        if file_path:
            df = read_excel(file_path)
        else:
            raise ValueError("DataFrame or valid file path must be provided to import_contacts")

    # If phone_col is still not resolved, attempt auto-detection
    if not phone_col:
        detected = detect_columns(df)
        phone_col = detected.get("phone") or (list(df.columns)[0] if len(df.columns) > 0 else "Phone")

    # Clean up column names if "(None)" or empty
    if name_col in ("", "(None)", "(None - Number Only)", None):
        name_col = None

    result = ImportResult()
    seen_phones: dict[str, int] = {}  # phone_e164 -> row index of canonical (first) occurrence

    for idx, row in df.iterrows():
        result.total += 1
        phone_raw = _cell(row.get(phone_col)) if phone_col and phone_col in row else ""

        # Handle contact name:
        # If a name column was explicitly mapped, use value from row
        # If no name column was mapped (number-only mode), default to phone_raw so it passes validation
        if name_col is not None and name_col in row:
            name = _cell(row.get(name_col))
        elif name_col is None:
            name = phone_raw or "Contact"
        else:
            name = ""

        email = _cell(row.get(email_col)) if email_col and email_col in row else None
        extra = {str(k): v for k, v in row.items() if k not in (name_col, phone_col, email_col)}

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
            source_file=source_filename,
            is_valid=is_valid,
            validation_error=error,
        )

        if is_valid:
            result.valid += 1
        elif error and (error.startswith("Duplicate") or error == "Already exists in contacts"):
            result.duplicates += 1
        else:
            result.invalid += 1

        result.rows.append(
            {"contact_id": contact_id, "row": idx + 2, "name": name, "phone": phone_raw, "is_valid": is_valid, "error": error}
        )

    return result
