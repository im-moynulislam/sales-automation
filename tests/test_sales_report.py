"""Full test suite for sales_report.py.

Run with:  python -m pytest test_sales_report.py -v

Sections
    1. Helpers
    2. Happy path
    3. Quantity validation
    4. Price validation
    5. Product validation
    6. Order ID validation
    7. Multiple error reasons
    8. Duplicate order IDs
    9. Columns and headers
   10. Empty files
   11. File and CSV errors
   12. Output files
   13. Summary calculation
   14. Console output
   15. Unit tests for the helper functions
   16. Command line (main)
   17. Cleanup checks (no leftover API code)
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import sales_report
from sales_report import (
    calculate_sales_summary,
    create_sales_report,
    get_error_reason,
    read_sales_csv,
    validate_sales_data,
)

HEADER = "order_id,product,quantity,price"


# ---------------------------------------------------------------------------
# 1. Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def input_file(tmp_path):
    return tmp_path / "sales.csv"


@pytest.fixture
def output_folder(tmp_path):
    return tmp_path / "output"


def write_csv(path, *rows, header=HEADER):
    """Write a CSV made of a header line and the given raw row strings."""
    path.write_text("\n".join([header, *rows]) + "\n")


def run(input_file, output_folder, *rows, header=HEADER):
    """Write the rows to input_file and run the report."""
    write_csv(input_file, *rows, header=header)
    create_sales_report(input_file, output_folder)


def read_processed(out):
    return pd.read_csv(out / "sales_processed.csv", dtype={"order_id": "string"})


def read_errors(out):
    return pd.read_csv(out / "sales_errors.csv", dtype={"order_id": "string"})


def read_summary(out):
    # keep_default_na=False so the text "N/A" is not turned into NaN
    return pd.read_csv(out / "summary.csv", keep_default_na=False)


def no_output_files(out):
    """True when none of the three report files were written."""
    return not any(
        (out / name).exists()
        for name in ("sales_processed.csv", "sales_errors.csv", "summary.csv")
    )


# ---------------------------------------------------------------------------
# 2. Happy path
# ---------------------------------------------------------------------------

def test_valid_sales_record(input_file, output_folder):
    run(input_file, output_folder, "101,Laptop,2,500")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 1
    assert processed.loc[0, "total_price"] == 1000
    assert len(errors) == 0


def test_multiple_valid_records(input_file, output_folder):
    run(
        input_file,
        output_folder,
        "1,Laptop,2,500",
        "2,Mouse,1,20",
        "3,Keyboard,3,30",
    )
    processed = read_processed(output_folder)
    assert len(processed) == 3
    assert processed["total_price"].tolist() == [1000, 20, 90]


def test_decimal_price_is_accepted(input_file, output_folder):
    run(input_file, output_folder, "1,Pen,3,19.99")
    processed = read_processed(output_folder)
    assert processed.loc[0, "total_price"] == pytest.approx(59.97)


def test_whole_number_quantity_written_as_float_is_accepted(input_file, output_folder):
    run(input_file, output_folder, "1,Pen,2.0,10")
    assert len(read_processed(output_folder)) == 1


def test_scientific_notation_quantity_is_accepted(input_file, output_folder):
    run(input_file, output_folder, "1,Pen,1e3,2")
    processed = read_processed(output_folder)
    assert len(processed) == 1
    assert processed.loc[0, "total_price"] == 2000


def test_alphanumeric_order_id_is_accepted(input_file, output_folder):
    run(input_file, output_folder, "ORD101,Laptop,2,500")
    processed = read_processed(output_folder)
    assert len(processed) == 1
    assert processed.loc[0, "order_id"] == "ORD101"
    assert len(read_errors(output_folder)) == 0


def test_leading_zeros_in_order_id_are_kept(input_file, output_folder):
    run(input_file, output_folder, "00101,Laptop,2,500")
    assert read_processed(output_folder).loc[0, "order_id"] == "00101"


def test_product_with_spaces_inside_name_is_kept(input_file, output_folder):
    run(input_file, output_folder, "1,Gaming Laptop,1,900")
    assert read_processed(output_folder).loc[0, "product"] == "Gaming Laptop"


def test_mixed_valid_and_invalid_records(input_file, output_folder):
    run(
        input_file,
        output_folder,
        "1,Laptop,2,500",   # valid
        "2,Mouse,0,20",     # invalid quantity
        "3,Keyboard,3,-1",  # invalid price
        "4,,1,10",          # missing product
        "5,Monitor,1,150",  # valid
    )
    assert read_processed(output_folder)["order_id"].tolist() == ["1", "5"]
    assert read_errors(output_folder)["order_id"].tolist() == ["2", "3", "4"]


def test_error_rows_keep_their_original_order(input_file, output_folder):
    run(input_file, output_folder, "9,A,0,1", "3,B,0,1", "7,C,0,1")
    assert read_errors(output_folder)["order_id"].tolist() == ["9", "3", "7"]


# ---------------------------------------------------------------------------
# 3. Quantity validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "quantity",
    ["0", "-1", "-2", "-10", "1.5", "0.5", "abc", "", "inf", "-inf", "Infinity", "nan", "NaN"],
)
def test_invalid_quantity_is_rejected(input_file, output_folder, quantity):
    run(input_file, output_folder, f"102,Laptop,{quantity},500")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Invalid quantity"


def test_one_bad_quantity_does_not_affect_other_rows(input_file, output_folder):
    run(input_file, output_folder, "1,A,inf,5", "2,B,1,5")
    assert read_processed(output_folder)["order_id"].tolist() == ["2"]
    assert read_errors(output_folder)["order_id"].tolist() == ["1"]


# ---------------------------------------------------------------------------
# 4. Price validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "price",
    ["-500", "-1000", "-0.01", "0", "abc", "", "inf", "-inf", "Infinity", "nan", "NaN"],
)
def test_invalid_price_is_rejected(input_file, output_folder, price):
    run(input_file, output_folder, f"103,Laptop,2,{price}")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Invalid price"


def test_very_small_positive_price_is_accepted(input_file, output_folder):
    run(input_file, output_folder, "1,Sticker,1,0.01")
    assert len(read_processed(output_folder)) == 1


# ---------------------------------------------------------------------------
# 5. Product validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("product", ["", "  ", "     "])
def test_missing_product_is_rejected(input_file, output_folder, product):
    run(input_file, output_folder, f"104,{product},2,500")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Missing product"


def test_product_whitespace_is_normalized_in_summary(input_file, output_folder):
    run(input_file, output_folder, "101,Laptop,2,500", "102, Laptop ,1,300")

    processed = read_processed(output_folder)
    summary = read_summary(output_folder)

    assert len(processed) == 2
    assert processed["product"].tolist() == ["Laptop", "Laptop"]
    assert summary.loc[0, "Total Revenue"] == 1300
    assert summary.loc[0, "Highest Revenue Product"] == "Laptop"


# ---------------------------------------------------------------------------
# 6. Order ID validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "order_id, should_be_valid",
    [
        ("101", True),
        ("00101", True),
        ("ORD101", True),
        ("BD-ORD-2026-001", True),
        ("", False),
        ("   ", False),
    ],
)
def test_order_id_formats(input_file, output_folder, order_id, should_be_valid):
    run(input_file, output_folder, f"{order_id},Laptop,2,500")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    if should_be_valid:
        assert len(processed) == 1
        assert processed.loc[0, "order_id"] == order_id
        assert len(errors) == 0
    else:
        assert len(processed) == 0
        assert len(errors) == 1
        assert errors.loc[0, "error_reason"] == "Missing order ID"


def test_missing_order_id_does_not_block_other_rows(input_file, output_folder):
    run(input_file, output_folder, ",Laptop,2,500", "102,Mouse,1,20")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 1
    assert len(errors) == 1
    assert pd.isna(errors.loc[0, "order_id"])


def test_two_missing_order_ids_are_not_duplicates(input_file, output_folder):
    run(input_file, output_folder, ",Laptop,2,500", "   ,Mouse,1,20")

    errors = read_errors(output_folder)
    assert len(errors) == 2
    assert errors["error_reason"].tolist() == ["Missing order ID", "Missing order ID"]


# ---------------------------------------------------------------------------
# 7. Multiple error reasons in one row
# ---------------------------------------------------------------------------

def test_row_with_all_problems_lists_every_reason_in_order(input_file, output_folder):
    run(input_file, output_folder, ",,0,-5")
    reason = read_errors(output_folder).loc[0, "error_reason"]
    assert reason == (
        "Invalid quantity; Invalid price; Missing product; Missing order ID"
    )


def test_quantity_and_price_both_invalid(input_file, output_folder):
    run(input_file, output_folder, "1,Laptop,inf,nan")
    reason = read_errors(output_folder).loc[0, "error_reason"]
    assert reason == "Invalid quantity; Invalid price"


def test_invalid_row_never_gets_duplicate_reason(input_file, output_folder):
    # Only valid rows are checked for duplicates, so the second row is
    # reported for its quantity only.
    run(input_file, output_folder, "A1,X,1,5", "A1,Y,0,5")
    errors = read_errors(output_folder)
    assert errors["error_reason"].tolist() == ["Invalid quantity"]


# ---------------------------------------------------------------------------
# 8. Duplicate order IDs
# ---------------------------------------------------------------------------

def test_duplicate_order_id_is_rejected(input_file, output_folder):
    run(input_file, output_folder, "105,Laptop,2,500", "105,Mouse,1,20")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 1
    assert processed.loc[0, "product"] == "Laptop"  # first one is kept
    assert len(errors) == 1
    assert errors.loc[0, "product"] == "Mouse"
    assert errors.loc[0, "error_reason"] == "Duplicate order ID"


def test_order_ids_with_trailing_whitespace_are_duplicates(input_file, output_folder):
    run(input_file, output_folder, "101,Laptop,2,500", "101 ,Mouse,1,20")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert len(processed) == 1
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Duplicate order ID"


def test_order_ids_with_leading_whitespace_are_duplicates(input_file, output_folder):
    run(input_file, output_folder, " A1,X,1,5", "A1,Y,1,5")

    assert read_processed(output_folder).loc[0, "product"] == "X"
    assert read_errors(output_folder).loc[0, "error_reason"] == "Duplicate order ID"


def test_three_rows_with_same_id_give_two_errors(input_file, output_folder):
    run(input_file, output_folder, "7,A,1,5", "7,B,1,5", "7,C,1,5")

    assert read_processed(output_folder)["product"].tolist() == ["A"]
    assert read_errors(output_folder)["product"].tolist() == ["B", "C"]


def test_invalid_first_row_does_not_make_valid_row_a_duplicate(input_file, output_folder):
    # First A1 is invalid (quantity 0); the second is valid and must be kept.
    run(input_file, output_folder, "A1,X,0,5", "A1,Y,1,5")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)

    assert processed["product"].tolist() == ["Y"]
    assert errors["error_reason"].tolist() == ["Invalid quantity"]


def test_order_id_is_case_sensitive(input_file, output_folder):
    run(input_file, output_folder, "ord1,A,1,5", "ORD1,B,1,5")
    assert len(read_processed(output_folder)) == 2
    assert len(read_errors(output_folder)) == 0


def test_ids_with_different_leading_zeros_are_different(input_file, output_folder):
    run(input_file, output_folder, "101,A,1,5", "0101,B,1,5")
    assert len(read_processed(output_folder)) == 2


def test_duplicates_are_not_counted_in_revenue(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,100", "1,A,1,100")
    assert read_summary(output_folder).loc[0, "Total Revenue"] == 100


# ---------------------------------------------------------------------------
# 9. Columns and headers
# ---------------------------------------------------------------------------

def test_clean_column_whitespace(tmp_path):
    csv_file = tmp_path / "sales.csv"
    csv_file.write_text("order_id, product ,quantity, price \n101,Keyboard,2,50\n")

    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()

    assert list(df.columns) == ["order_id", "product", "quantity", "price"]


def test_create_sales_report_with_whitespace_columns(input_file, output_folder):
    input_file.write_text(
        "order_id, product ,quantity, price \n"
        "101,Keyboard,2,50\n"
        "101,Mouse,1,30\n"
    )
    create_sales_report(input_file, output_folder)

    assert (output_folder / "sales_processed.csv").exists()
    assert (output_folder / "sales_errors.csv").exists()
    assert (output_folder / "summary.csv").exists()

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    assert len(processed) == 1
    assert processed.loc[0, "order_id"] == 101
    assert processed.loc[0, "product"] == "Keyboard"

    errors = pd.read_csv(output_folder / "sales_errors.csv")
    assert len(errors) == 1
    assert errors.loc[0, "order_id"] == 101
    assert "duplicate" in errors.loc[0, "error_reason"].lower()


def test_whitespace_in_order_id_header_does_not_crash(input_file, output_folder):
    # A space in the order_id header used to break the .str.strip() call.
    run(input_file, output_folder, "1,A,1,5", header=" order_id,product,quantity,price")
    assert read_processed(output_folder)["order_id"].tolist() == ["1"]


def test_columns_in_different_order(input_file, output_folder):
    run(input_file, output_folder, "5,2,Laptop,1", header="price,quantity,product,order_id")
    processed = read_processed(output_folder)
    assert processed.loc[0, "order_id"] == "1"
    assert processed.loc[0, "total_price"] == 10


def test_extra_columns_are_kept_in_outputs(input_file, output_folder):
    run(
        input_file,
        output_folder,
        "1,A,1,5,fast",
        "2,B,0,5,slow",
        header=HEADER + ",notes",
    )
    assert read_processed(output_folder).loc[0, "notes"] == "fast"
    assert read_errors(output_folder).loc[0, "notes"] == "slow"


@pytest.mark.parametrize(
    "columns, missing",
    [
        (["order_id", "product", "quantity"], ["price"]),
        (["order_id", "product", "price"], ["quantity"]),
        (["order_id", "quantity", "price"], ["product"]),
        (["product", "quantity", "price"], ["order_id"]),
        (["order_id", "product"], ["price", "quantity"]),
        (["a", "b"], ["order_id", "price", "product", "quantity"]),
    ],
)
def test_missing_required_columns_with_data_rows(
    input_file, output_folder, capsys, columns, missing
):
    row = ",".join("1" for _ in columns)
    input_file.write_text(",".join(columns) + "\n" + row + "\n" + row + "\n")

    create_sales_report(input_file, output_folder)

    printed = capsys.readouterr().out
    assert "Missing required columns" in printed
    assert str(sorted(missing)) in printed
    assert no_output_files(output_folder)


def test_missing_order_id_column_with_data_rows(input_file, output_folder, capsys):
    input_file.write_text("product,quantity,price\nLaptop,2,500\nMouse,1,20\n")

    create_sales_report(input_file, output_folder)

    printed = capsys.readouterr().out
    assert "Missing required columns" in printed
    assert "order_id" in printed
    assert no_output_files(output_folder)


@pytest.mark.parametrize(
    "columns",
    [
        ["order_id", "product", "quantity"],
        ["order_id", "product", "price"],
        ["order_id", "quantity", "price"],
    ],
)
def test_missing_required_columns_with_no_rows(input_file, output_folder, columns):
    pd.DataFrame(columns=columns).to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    assert no_output_files(output_folder)


def test_column_names_are_case_sensitive(input_file, output_folder, capsys):
    run(input_file, output_folder, "1,A,1,5", header="Order_ID,Product,Quantity,Price")
    assert "Missing required columns" in capsys.readouterr().out
    assert no_output_files(output_folder)


# ---------------------------------------------------------------------------
# 10. Empty files
# ---------------------------------------------------------------------------

def test_completely_empty_file(input_file, output_folder, capsys):
    input_file.write_text("")
    create_sales_report(input_file, output_folder)

    assert "is empty" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_file_with_only_whitespace(input_file, output_folder, capsys):
    input_file.write_text("\n\n   \n")
    create_sales_report(input_file, output_folder)

    assert "Error" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_headers_only(input_file, output_folder, capsys):
    input_file.write_text(HEADER + "\n")
    create_sales_report(input_file, output_folder)

    assert "no sales records" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_headers_only_with_missing_columns_reports_no_records(
    input_file, output_folder, capsys
):
    input_file.write_text("order_id,product\n")
    create_sales_report(input_file, output_folder)

    assert "no sales records" in capsys.readouterr().out
    assert no_output_files(output_folder)


# ---------------------------------------------------------------------------
# 11. File and CSV errors
# ---------------------------------------------------------------------------

def test_missing_input_file(tmp_path, output_folder, capsys):
    create_sales_report(tmp_path / "does_not_exist.csv", output_folder)

    assert "Could not find" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_input_path_is_a_directory(tmp_path, output_folder, capsys):
    create_sales_report(tmp_path, output_folder)

    assert "Error" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_malformed_csv(input_file, output_folder, capsys):
    input_file.write_text("a,b,c,d\n1,A,1,2\n2,B,1,2,3,4,5\n")
    create_sales_report(input_file, output_folder)

    assert "not a well-formed CSV" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_bad_encoding(input_file, output_folder, capsys):
    input_file.write_bytes(b"order_id,product,quantity,price\n1,\xff\xfe,1,5\n")
    create_sales_report(input_file, output_folder)

    assert "bad encoding" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_permission_error_is_handled(input_file, output_folder, capsys, monkeypatch):
    def deny(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(pd, "read_csv", deny)
    create_sales_report(input_file, output_folder)

    assert "No permission" in capsys.readouterr().out
    assert no_output_files(output_folder)


def test_other_os_error_is_handled(input_file, output_folder, capsys, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("disk problem")

    monkeypatch.setattr(pd, "read_csv", fail)
    create_sales_report(input_file, output_folder)

    printed = capsys.readouterr().out
    assert "Could not read" in printed
    assert "disk problem" in printed
    assert no_output_files(output_folder)


def test_read_sales_csv_returns_dataframe_for_good_file(input_file):
    write_csv(input_file, "1,A,1,5")
    df = read_sales_csv(input_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_read_sales_csv_returns_none_for_bad_file(tmp_path):
    assert read_sales_csv(tmp_path / "missing.csv") is None


def test_order_id_column_is_read_as_text(input_file):
    write_csv(input_file, "00101,A,1,5")
    assert read_sales_csv(input_file).loc[0, "order_id"] == "00101"


# ---------------------------------------------------------------------------
# 12. Output files
# ---------------------------------------------------------------------------

def test_output_folder_is_created_including_parents(input_file, tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    run(input_file, nested, "1,A,1,5")
    assert (nested / "summary.csv").exists()


def test_all_three_files_are_written(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,5")
    for name in ("sales_processed.csv", "sales_errors.csv", "summary.csv"):
        assert (output_folder / name).exists()


def test_errors_file_has_reason_column_even_when_no_errors(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,5")
    errors = read_errors(output_folder)
    assert len(errors) == 0
    assert "error_reason" in errors.columns


def test_processed_file_has_total_price_and_no_error_reason(input_file, output_folder):
    run(input_file, output_folder, "1,A,2,5")
    processed = read_processed(output_folder)
    assert "total_price" in processed.columns
    assert "error_reason" not in processed.columns


def test_summary_has_expected_columns(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,5")
    assert list(read_summary(output_folder).columns) == [
        "Total Revenue",
        "Valid Records",
        "Invalid Records",
        "Average Sale Value",
        "Highest Revenue Product",
        "Most Units Sold Product",
    ]


def test_all_records_invalid(input_file, output_folder):
    run(input_file, output_folder, "301,Laptop,-1,100", "302,,0,-50")

    processed = read_processed(output_folder)
    errors = read_errors(output_folder)
    summary = read_summary(output_folder)

    assert len(processed) == 0
    assert len(errors) == 2
    assert summary.loc[0, "Valid Records"] == 0
    assert summary.loc[0, "Invalid Records"] == 2
    assert summary.loc[0, "Total Revenue"] == 0
    assert summary.loc[0, "Average Sale Value"] == 0
    assert summary.loc[0, "Highest Revenue Product"] == "N/A"
    assert summary.loc[0, "Most Units Sold Product"] == "N/A"


def test_running_twice_overwrites_old_results(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,5", "2,B,1,5")
    run(input_file, output_folder, "9,Z,1,7")

    processed = read_processed(output_folder)
    assert processed["order_id"].tolist() == ["9"]
    assert read_summary(output_folder).loc[0, "Valid Records"] == 1


def test_input_file_is_not_modified(input_file, output_folder):
    write_csv(input_file, "1, A ,1,5", "1,B,0,5")
    before = input_file.read_text()

    create_sales_report(input_file, output_folder)

    assert input_file.read_text() == before


def test_windows_line_endings(input_file, output_folder):
    input_file.write_bytes(b"order_id,product,quantity,price\r\n1,A,2,5\r\n2,B,1,3\r\n")
    create_sales_report(input_file, output_folder)
    assert len(read_processed(output_folder)) == 2


def test_file_with_utf8_bom(input_file, output_folder):
    input_file.write_bytes(
        b"\xef\xbb\xbforder_id,product,quantity,price\n1,A,2,5\n"
    )
    create_sales_report(input_file, output_folder)
    assert len(read_processed(output_folder)) == 1


def test_non_english_product_names(input_file, output_folder):
    input_file.write_text(
        HEADER + "\n1,কলম,2,10\n", encoding="utf-8"
    )
    create_sales_report(input_file, output_folder)
    assert read_processed(output_folder).loc[0, "product"] == "কলম"


def test_blank_lines_between_rows_are_ignored(input_file, output_folder):
    input_file.write_text(HEADER + "\n1,A,1,5\n\n2,B,1,5\n")
    create_sales_report(input_file, output_folder)
    assert len(read_processed(output_folder)) == 2


# ---------------------------------------------------------------------------
# 13. Summary calculation
# ---------------------------------------------------------------------------

def test_sales_summary_calculation(input_file, output_folder):
    run(
        input_file,
        output_folder,
        "201,Laptop,2,500",
        "202,Mouse,1,20",
        "203,Keyboard,3,30",
    )
    summary = read_summary(output_folder)
    total = 500 * 2 + 20 * 1 + 30 * 3

    assert summary.loc[0, "Total Revenue"] == total
    assert summary.loc[0, "Valid Records"] == 3
    assert summary.loc[0, "Invalid Records"] == 0
    assert summary.loc[0, "Average Sale Value"] == pytest.approx(total / 3)
    assert summary.loc[0, "Highest Revenue Product"] == "Laptop"
    assert summary.loc[0, "Most Units Sold Product"] == "Keyboard"


def test_top_revenue_and_top_units_can_be_different_products(input_file, output_folder):
    run(input_file, output_folder, "1,Laptop,1,1000", "2,Pen,50,2")
    summary = read_summary(output_folder)
    assert summary.loc[0, "Highest Revenue Product"] == "Laptop"
    assert summary.loc[0, "Most Units Sold Product"] == "Pen"


def test_same_product_on_many_rows_is_added_together(input_file, output_folder):
    run(input_file, output_folder, "1,Pen,10,1", "2,Pen,10,1", "3,Book,1,15")
    summary = read_summary(output_folder)
    assert summary.loc[0, "Highest Revenue Product"] == "Pen"  # 20 vs 15
    assert summary.loc[0, "Most Units Sold Product"] == "Pen"


def test_invalid_rows_are_left_out_of_the_summary(input_file, output_folder):
    run(input_file, output_folder, "1,A,2,10", "2,B,0,999", "3,C,1,inf")
    summary = read_summary(output_folder)
    assert summary.loc[0, "Total Revenue"] == 20
    assert summary.loc[0, "Valid Records"] == 1
    assert summary.loc[0, "Invalid Records"] == 2


def test_average_sale_value_with_decimals(input_file, output_folder):
    run(input_file, output_folder, "1,A,1,10.50", "2,B,1,20.25")
    summary = read_summary(output_folder)
    assert summary.loc[0, "Average Sale Value"] == pytest.approx(15.375)


# ---------------------------------------------------------------------------
# 14. Console output
# ---------------------------------------------------------------------------

def test_report_complete_message(input_file, output_folder, capsys):
    run(input_file, output_folder, "1,Laptop,2,500", "2,Mouse,0,20")

    printed = capsys.readouterr().out
    assert "Report complete: 1 valid, 1 invalid, total revenue = 1000.00" in printed


def test_summary_table_is_printed(input_file, output_folder, capsys):
    run(input_file, output_folder, "1,Laptop,2,500")

    printed = capsys.readouterr().out
    assert "Total Revenue" in printed
    assert "Highest Revenue Product" in printed
    assert "Laptop" in printed


def test_error_messages_are_not_printed_for_good_file(input_file, output_folder, capsys):
    run(input_file, output_folder, "1,Laptop,2,500")
    assert "Error" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 15. Unit tests for the helper functions
# ---------------------------------------------------------------------------

def make_df(rows):
    return pd.DataFrame(rows, columns=["order_id", "product", "quantity", "price"])


def test_validate_returns_all_expected_keys():
    result = validate_sales_data(make_df([["1", "A", "1", "5"]]))
    assert set(result) == {
        "invalid_rows",
        "invalid_quantity",
        "invalid_price",
        "invalid_products",
        "invalid_duplicates",
        "invalid_order_ids",
    }


def test_validate_flags_each_problem_separately():
    df = make_df(
        [
            ["1", "A", "1", "5"],      # 0 valid
            ["2", "A", "0", "5"],      # 1 bad quantity
            ["3", "A", "1", "-5"],     # 2 bad price
            ["4", "  ", "1", "5"],     # 3 bad product
            ["  ", "A", "1", "5"],     # 4 bad order id
        ]
    )
    result = validate_sales_data(df)

    assert result["invalid_quantity"].tolist() == [False, True, False, False, False]
    assert result["invalid_price"].tolist() == [False, False, True, False, False]
    assert result["invalid_products"].tolist() == [False, False, False, True, False]
    assert result["invalid_order_ids"].tolist() == [False, False, False, False, True]
    assert result["invalid_rows"].tolist() == [False, True, True, True, True]


def test_validate_rejects_infinity_and_nan_directly():
    df = make_df(
        [
            ["1", "A", float("inf"), 5],
            ["2", "A", float("-inf"), 5],
            ["3", "A", float("nan"), 5],
            ["4", "A", 1, float("inf")],
            ["5", "A", 1, float("-inf")],
            ["6", "A", 1, float("nan")],
        ]
    )
    result = validate_sales_data(df)
    assert result["invalid_quantity"].tolist() == [True, True, True, False, False, False]
    assert result["invalid_price"].tolist() == [False, False, False, True, True, True]
    assert result["invalid_rows"].all()


def test_validate_normalises_whitespace_before_checking_duplicates():
    df = make_df([[" A1", "X", "1", "5"], ["A1 ", "Y", "1", "5"]])
    result = validate_sales_data(df)
    assert result["invalid_rows"].tolist() == [False, True]
    assert result["invalid_duplicates"].index.tolist() == [1]


def test_validate_only_checks_duplicates_among_valid_rows():
    df = make_df([["A1", "X", "0", "5"], ["A1", "Y", "1", "5"], ["A1", "Z", "1", "5"]])
    result = validate_sales_data(df)
    assert result["invalid_rows"].tolist() == [True, False, True]
    assert result["invalid_duplicates"].index.tolist() == [2]


def test_validate_handles_missing_values():
    df = make_df([[None, None, None, None]])
    result = validate_sales_data(df)
    assert result["invalid_rows"].tolist() == [True]
    assert result["invalid_quantity"].tolist() == [True]
    assert result["invalid_price"].tolist() == [True]
    assert result["invalid_products"].tolist() == [True]
    assert result["invalid_order_ids"].tolist() == [True]


def test_get_error_reason_for_each_flag():
    row = pd.Series({"x": 1}, name=0)
    yes = pd.Series([True], index=[0])
    no = pd.Series([False], index=[0])
    none = pd.DataFrame(index=[])

    assert get_error_reason(row, yes, no, no, none, no) == "Invalid quantity"
    assert get_error_reason(row, no, yes, no, none, no) == "Invalid price"
    assert get_error_reason(row, no, no, yes, none, no) == "Missing product"
    assert get_error_reason(row, no, no, no, none, yes) == "Missing order ID"
    assert get_error_reason(row, no, no, no, pd.DataFrame(index=[0]), no) == "Duplicate order ID"
    assert get_error_reason(row, no, no, no, none, no) == ""


def test_get_error_reason_joins_several_reasons():
    row = pd.Series({"x": 1}, name=0)
    yes = pd.Series([True], index=[0])
    assert (
        get_error_reason(row, yes, yes, yes, pd.DataFrame(index=[0]), yes)
        == "Invalid quantity; Invalid price; Missing product; "
           "Missing order ID; Duplicate order ID"
    )


def test_calculate_summary_with_empty_dataframe():
    empty = pd.DataFrame(columns=["product", "quantity", "price", "total_price"])
    summary = calculate_sales_summary(empty)
    assert summary == {
        "total_revenue": 0,
        "average_sale_value": 0,
        "highest_revenue_product": "N/A",
        "most_units_sold_product": "N/A",
    }


def test_calculate_summary_values():
    df = pd.DataFrame(
        {
            "product": ["A", "B", "A"],
            "quantity": [1, 10, 1],
            "price": [100, 1, 50],
            "total_price": [100, 10, 50],
        }
    )
    summary = calculate_sales_summary(df)
    assert summary["total_revenue"] == 160
    assert summary["average_sale_value"] == pytest.approx(160 / 3)
    assert summary["highest_revenue_product"] == "A"
    assert summary["most_units_sold_product"] == "B"


# ---------------------------------------------------------------------------
# 16. Command line (main)
# ---------------------------------------------------------------------------

def test_main_with_both_arguments(input_file, output_folder, monkeypatch):
    write_csv(input_file, "1,A,1,5")
    monkeypatch.setattr(
        sys, "argv", ["sales_report.py", str(input_file), str(output_folder)]
    )
    sales_report.main()
    assert (output_folder / "summary.csv").exists()


def test_main_uses_default_output_folder(input_file, tmp_path, monkeypatch):
    write_csv(input_file, "1,A,1,5")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sales_report.py", str(input_file)])
    sales_report.main()
    assert (tmp_path / "output" / "summary.csv").exists()


def test_main_without_arguments_exits_with_usage_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sales_report.py"])
    with pytest.raises(SystemExit) as error:
        sales_report.main()
    assert error.value.code == 2


def test_script_runs_from_command_line(input_file, output_folder):
    write_csv(input_file, "1,A,2,5")
    script = Path(sales_report.__file__)

    result = subprocess.run(
        [sys.executable, str(script), str(input_file), str(output_folder)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Report complete: 1 valid, 0 invalid" in result.stdout
    assert (output_folder / "sales_processed.csv").exists()


def test_importing_the_module_does_not_run_the_report(capsys):
    # Importing must be silent; main() only runs from the command line.
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# 17. Cleanup checks (no leftover API code)
# ---------------------------------------------------------------------------

def test_api_code_removed():
    assert not hasattr(sales_report, "API_KEY")
    assert not hasattr(sales_report, "load_dotenv")
    assert not hasattr(sales_report, "os")


def test_source_has_no_dotenv_or_api_key_text():
    source = Path(sales_report.__file__).read_text()
    assert "dotenv" not in source
    assert "API_KEY" not in source