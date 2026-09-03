"""Phone number normalization/validation for Indian mobile numbers."""
import re
from typing import Optional

from app.config import INDIAN_MOBILE_REGEX

_PHONE_PATTERN = re.compile(INDIAN_MOBILE_REGEX)


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    """Returns canonical +91XXXXXXXXXX form, or None if not a valid Indian mobile number."""
    if raw is None:
        return None
    digits_and_plus = re.sub(r"[^\d+]", "", str(raw).strip())
    match = _PHONE_PATTERN.match(digits_and_plus)
    if not match:
        return None
    return f"+91{match.group(1)}"


def validate_contact(name: Optional[str], phone_raw: Optional[str]) -> tuple[bool, Optional[str], Optional[str]]:
    """Returns (is_valid, phone_e164_or_None, human_readable_error_or_None)."""
    def _clean(value) -> str:
        if value is None or (isinstance(value, float) and value != value):  # NaN != NaN
            return ""
        return str(value).strip()

    name = _clean(name)
    phone_raw_str = _clean(phone_raw)

    if not name:
        return False, None, "Missing name"
    if not phone_raw_str:
        return False, None, "Missing phone number"

    phone_e164 = normalize_phone(phone_raw_str)
    if phone_e164 is None:
        return False, None, "Invalid phone number format"

    return True, phone_e164, None
