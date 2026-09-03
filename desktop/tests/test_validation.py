from app.services.validation import normalize_phone, validate_contact


def test_normalize_plain_10_digit():
    assert normalize_phone("9876543210") == "+919876543210"


def test_normalize_with_plus91_prefix():
    assert normalize_phone("+919876543210") == "+919876543210"


def test_normalize_with_91_prefix_no_plus():
    assert normalize_phone("919876543210") == "+919876543210"


def test_normalize_strips_spaces_and_dashes():
    assert normalize_phone(" 98765-43210 ") == "+919876543210"


def test_normalize_rejects_invalid_leading_digit():
    assert normalize_phone("5876543210") is None  # must start with 6-9


def test_normalize_rejects_too_short():
    assert normalize_phone("98765") is None


def test_normalize_rejects_letters():
    assert normalize_phone("98765abcde") is None


def test_normalize_rejects_none():
    assert normalize_phone(None) is None


def test_validate_contact_missing_name():
    is_valid, phone, error = validate_contact("", "9876543210")
    assert is_valid is False
    assert error == "Missing name"


def test_validate_contact_missing_phone():
    is_valid, phone, error = validate_contact("Rahul", "")
    assert is_valid is False
    assert error == "Missing phone number"


def test_validate_contact_invalid_phone():
    is_valid, phone, error = validate_contact("Rahul", "12345")
    assert is_valid is False
    assert error == "Invalid phone number format"


def test_validate_contact_valid():
    is_valid, phone, error = validate_contact("Rahul Sharma", "9876543210")
    assert is_valid is True
    assert phone == "+919876543210"
    assert error is None
