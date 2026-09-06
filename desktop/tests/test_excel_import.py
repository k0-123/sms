import pandas as pd

from app.db.migrations import run_migrations
from app.services.excel_import import detect_columns, import_contacts, read_excel


def _write_fixture(tmp_path):
    df = pd.DataFrame(
        {
            "Name": ["Rahul Sharma", "Amit Singh", "Priya Verma", "Bad Row", "Dup Row", ""],
            "Phone Number": ["9876543210", "9876543211", "", "12345", "9876543210", "9876543212"],
        }
    )
    path = tmp_path / "contacts.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")
    return str(path)


def test_detect_columns_matches_name_and_phone(tmp_path):
    path = _write_fixture(tmp_path)
    df = read_excel(path)
    mapping = detect_columns(df)
    assert mapping["name"] == "Name"
    assert mapping["phone"] == "Phone Number"


def test_import_contacts_breakdown(tmp_path):
    run_migrations()
    path = _write_fixture(tmp_path)
    df = read_excel(path)
    result = import_contacts(path, df, name_col="Name", phone_col="Phone Number")

    assert result.total == 6
    # Rahul (valid), Amit (valid), Priya (missing phone -> invalid),
    # Bad Row (invalid format), Dup Row (duplicate of Rahul's number), blank name row (invalid)
    assert result.valid == 2
    assert result.invalid == 3
    assert result.duplicates == 1
    assert result.valid + result.invalid + result.duplicates == result.total


def test_import_never_drops_rows_all_persisted(tmp_path):
    run_migrations()
    path = _write_fixture(tmp_path)
    df = read_excel(path)
    result = import_contacts(path, df, name_col="Name", phone_col="Phone Number")
    assert len(result.rows) == 6
    assert all(r["contact_id"] for r in result.rows)


def test_import_contacts_number_only(tmp_path):
    run_migrations()
    df = pd.DataFrame({"Phone": ["9876543220", "9876543221", "12345"]})
    path = tmp_path / "numbers_only.csv"
    df.to_csv(path, index=False)
    
    loaded = read_excel(str(path))
    mapping = detect_columns(loaded)
    result = import_contacts(loaded, mapping, source_file=str(path))
    
    assert result.total == 3
    assert result.valid == 2
    assert result.invalid == 1
    assert result.duplicates == 0


def test_import_contacts_with_mapping_and_source_file_kwarg(tmp_path):
    run_migrations()
    df = pd.DataFrame({"Mobile": ["9876543230", "9876543231"]})
    path = tmp_path / "mobiles.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")
    
    loaded = read_excel(str(path))
    result = import_contacts(loaded, column_mapping={"phone": "Mobile"}, source_file=str(path))
    
    assert result.total == 2
    assert result.valid == 2

