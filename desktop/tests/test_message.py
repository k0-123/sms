from app.services.message import render, sms_part_count


def test_render_substitutes_name():
    assert render("Hello {name}, thanks.", "Rahul Sharma") == "Hello Rahul Sharma, thanks."


def test_sms_part_count_short_gsm7():
    chars, parts = sms_part_count("Hello there")
    assert chars == 11
    assert parts == 1


def test_sms_part_count_boundary_160():
    text = "a" * 160
    _, parts = sms_part_count(text)
    assert parts == 1


def test_sms_part_count_over_160_splits():
    text = "a" * 161
    _, parts = sms_part_count(text)
    assert parts == 2


def test_sms_part_count_unicode_uses_ucs2_limits():
    text = "नमस्ते" * 20  # Hindi, not in GSM-7 -> UCS-2 rules
    chars, parts = sms_part_count(text)
    assert parts >= 2
