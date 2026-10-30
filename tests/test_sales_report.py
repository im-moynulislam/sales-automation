from pathlib import Path
import pandas as pd
import pytest

from sales_report import create_sales_report


def test_valid_sales_record(tmp_path):
    # Arrange: create a small input CSV
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [101],
        "product": ["Laptop"],
        "quantity": [2],
        "price": [500]
    })

    df.to_csv(input_file, index=False)

    # Act: run the sales report function
    create_sales_report(input_file, output_folder)

    # Assert: check the exported result
    processed_file = output_folder / "sales_processed.csv"

    assert processed_file.exists()

    result = pd.read_csv(processed_file)

    assert len(result) == 1
    assert result.loc[0, "total_price"] == 1000

@pytest.mark.parametrize("quantity", [0, -2, -10])
def test_invalid_quantity_is_rejected(tmp_path, quantity):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [102],
        "product": ["Laptop"],
        "quantity": [quantity],
        "price": [500]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Invalid quantity"

@pytest.mark.parametrize("price", [-500, -1000, 0, "abc", None , ""])
def test_invalid_price_is_rejected(tmp_path, price):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [103],
        "product": ["Laptop"],
        "quantity": [2],
        "price": [price]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Invalid price"
@pytest.mark.parametrize("product", ["", None , "  "])
def test_missing_product_is_rejected(tmp_path, product):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [104],
        "product": [product],
        "quantity": [2],
        "price": [500]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Missing product"
def test_missing_product_is_rejected(tmp_path):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [104],
        "product": [""],
        "quantity": [2],
        "price": [500]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")

    assert len(processed) == 0
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Missing product"
def test_duplicate_order_id_is_rejected(tmp_path):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [105, 105],
        "product": ["Laptop", "Mouse"],
        "quantity": [2, 1],
        "price": [500, 20]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")

    assert len(processed) == 1
    assert len(errors) == 1
    assert errors.loc[0, "error_reason"] == "Duplicate order ID"
@pytest.mark.parametrize(
    "columns",
    [
        ["order_id", "product", "quantity"],  # Missing price
        ["order_id", "product", "price"],     # Missing quantity
        ["order_id", "quantity", "price"],    # Missing product
    ]
)
def test_missing_required_columns(tmp_path, columns):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame(columns=columns)
    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    assert not (output_folder / "sales_processed.csv").exists()
    assert not (output_folder / "sales_errors.csv").exists()
    assert not (output_folder / "summary.csv").exists()


@pytest.mark.parametrize(
    "empty_type",
    ["completely_empty", "headers_only"]
)
def test_empty_csv_is_rejected(tmp_path, empty_type):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    if empty_type == "completely_empty":
        input_file.write_text("")
    else:
        input_file.write_text(
            "order_id,product,quantity,price\n"
        )

    create_sales_report(input_file, output_folder)

    assert not (output_folder / "sales_processed.csv").exists()
    assert not (output_folder / "sales_errors.csv").exists()
    assert not (output_folder / "summary.csv").exists()

def test_sales_summary_calculation(tmp_path):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [201, 202, 203],
        "product": ["Laptop", "Mouse", "Keyboard"],
        "quantity": [2, 1, 3],
        "price": [500, 20, 30]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    summary = pd.read_csv(output_folder / "summary.csv")

    assert summary.loc[0, "Total Revenue"] == 500*2 + 20*1 + 30*3
    assert summary.loc[0, "Valid Records"] == 3
    assert summary.loc[0, "Invalid Records"] == 0
    assert summary.loc[0, "Average Sale Value"] == round((500*2 + 20*1 + 30*3) / 3, 2)
    assert summary.loc[0, "Most Units Sold Product"] == "Keyboard"

def test_all_records_invalid(tmp_path):
    input_file = tmp_path / "sales.csv"
    output_folder = tmp_path / "output"

    df = pd.DataFrame({
        "order_id": [301, 302],
        "product": ["Laptop", None],
        "quantity": [-1, 0],
        "price": [100, -50]
    })

    df.to_csv(input_file, index=False)

    create_sales_report(input_file, output_folder)

    processed = pd.read_csv(output_folder / "sales_processed.csv")
    errors = pd.read_csv(output_folder / "sales_errors.csv")
    summary = pd.read_csv(output_folder / "summary.csv")

    assert len(processed) == 0
    assert len(errors) == 2
    assert summary.loc[0, "Valid Records"] == 0
    assert summary.loc[0, "Invalid Records"] == 2