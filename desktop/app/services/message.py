"""Message personalization ({name} substitution) and SMS character/part counting."""
import math

# GSM 03.38 default alphabet (basic set only - good enough to distinguish
# "will fit in GSM-7 SMS" from "needs UCS-2" for warning purposes).
_GSM7_CHARS = (
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
_GSM7_SET = set(_GSM7_CHARS)


def render(template: str, name: str) -> str:
    return template.replace("{name}", name)


def is_gsm7(text: str) -> bool:
    return all(ch in _GSM7_SET for ch in text)


def sms_part_count(text: str) -> tuple[int, int]:
    """Returns (character_count, sms_part_count)."""
    length = len(text)
    if length == 0:
        return 0, 0
    if is_gsm7(text):
        single_limit, multi_limit = 160, 153
    else:
        single_limit, multi_limit = 70, 67
    if length <= single_limit:
        return length, 1
    return length, math.ceil(length / multi_limit)
