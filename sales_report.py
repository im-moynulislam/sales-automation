from pathlib import Path
import argparse

import numpy as np
import pandas as pd


def validate_sales_data(df):
    """Check every row of the sales data and flag the invalid ones.

    A row is invalid if its quantity is not a positive whole number, its price
    is not a positive number, or its product or order ID is blank. NaN,
    infinity and negative infinity are rejected for quantity and price.
    Duplicate order IDs are checked only among otherwise-valid rows, after
    stripping whitespace, so the first valid occurrence is kept.

    Returns a dictionary of boolean Series (and the duplicate rows DataFrame).
    """
    quantity_numeric = pd.to_numeric(df["quantity"], errors="coerce")
    invalid_quantity = (
        quantity_numeric.isna()
        | np.isinf(quantity_numeric)
        | (quantity_numeric <= 0)
        | (quantity_numeric % 1 != 0)
    )

    price_numeric = pd.to_numeric(df["price"], errors="coerce")
    invalid_price = (
        price_numeric.isna()
        | np.isinf(price_numeric)
        | (price_numeric <= 0)
    )

    product_text = df["product"].astype("string").fillna("")
    invalid_products = product_text.str.strip() == ""

    order_id_text = df["order_id"].astype("string").str.strip().fillna("")
    invalid_order_ids = order_id_text == ""

    invalid_data = (
        invalid_quantity
        | invalid_price
        | invalid_products
        | invalid_order_ids
    )

    # Duplicates are looked for only among valid rows, using cleaned IDs.
    valid_candidates = df[~invalid_data]
    duplicate_ids = order_id_text[~invalid_data].duplicated(keep="first")
    invalid_duplicates = valid_candidates[duplicate_ids].copy()

    invalid_rows = invalid_data.copy()
    invalid_rows.loc[invalid_duplicates.index] = True

    return {
        "invalid_rows": invalid_rows,
        "invalid_quantity": invalid_quantity,
        "invalid_price": invalid_price,
        "invalid_products": invalid_products,
        "invalid_duplicates": invalid_duplicates,
        "invalid_order_ids": invalid_order_ids,
    }


def calculate_sales_summary(valid_df):
    """Return total revenue, average sale value and the top products.

    Expects a DataFrame of valid rows that already has a total_price column.
    If the DataFrame is empty, the product fields are set to "N/A".
    """
    total_revenue = valid_df["total_price"].sum()

    revenue_by_product = (
        valid_df.groupby("product")["total_price"]
        .sum()
        .sort_values(ascending=False)
    )

    units_by_product = (
        valid_df.groupby("product")["quantity"]
        .sum()
        .sort_values(ascending=False)
    )

    average_sale_value = (
        total_revenue / len(valid_df)
        if not valid_df.empty
        else 0
    )

    if valid_df.empty:
        highest_revenue_product = "N/A"
        most_units_sold_product = "N/A"
    else:
        highest_revenue_product = revenue_by_product.idxmax()
        most_units_sold_product = units_by_product.idxmax()

    return {
        "total_revenue": total_revenue,
        "average_sale_value": average_sale_value,
        "highest_revenue_product": highest_revenue_product,
        "most_units_sold_product": most_units_sold_product,
    }


def get_error_reason(row, invalid_quantity, invalid_price, invalid_products, invalid_duplicates, invalid_order_ids):
    """Return all reasons a row is invalid, joined by "; "."""
    checks = [
        (invalid_quantity.loc[row.name], "Invalid quantity"),
        (invalid_price.loc[row.name], "Invalid price"),
        (invalid_products.loc[row.name], "Missing product"),
        (invalid_order_ids.loc[row.name], "Missing order ID"),
        (row.name in invalid_duplicates.index, "Duplicate order ID"),
    ]
    return "; ".join(reason for failed, reason in checks if failed)


def export_sales_reports(valid_df, invalid_df, export_summary, output_path):
    """Write the error, processed and summary CSV files to output_path."""
    invalid_df.to_csv(output_path / "sales_errors.csv", index=False)
    valid_df.to_csv(output_path / "sales_processed.csv", index=False)
    export_summary.to_csv(output_path / "summary.csv", index=False)


def read_sales_csv(input_file):
    """Read the sales CSV and return a DataFrame, or None if it cannot be used.

    Prints a clear message instead of crashing when the file is missing,
    unreadable, empty, malformed or not valid text.
    """
    try:
        return pd.read_csv(input_file, dtype={"order_id": "string"})
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'.")
    except PermissionError:
        print(f"Error: No permission to read '{input_file}'.")
    except pd.errors.EmptyDataError:
        print(f"Error: '{input_file}' is empty.")
    except pd.errors.ParserError as error:
        print(f"Error: '{input_file}' is not a well-formed CSV file ({error}).")
    except UnicodeDecodeError:
        print(f"Error: '{input_file}' could not be read as text (bad encoding).")
    except OSError as error:
        print(f"Error: Could not read '{input_file}' ({error}).")
    return None


def create_sales_report(input_file, output_folder):
    """Read a sales CSV, validate it and write the cleaned reports."""
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    df = read_sales_csv(input_file)
    if df is None:
        return

    if df.empty:
        print(f"Error: '{input_file}' has headers but no sales records.")
        return

    df.columns = df.columns.str.strip()
    required_columns = {
        "order_id",
        "product",
        "quantity",
        "price",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        print(f"Error: Missing required columns: {sorted(missing_columns)}")
        return

    # Clean whitespace first so validation and duplicate checks see clean values.
    df["order_id"] = df["order_id"].astype("string").str.strip()
    df["product"] = df["product"].astype("string").str.strip()
    validation = validate_sales_data(df)

    invalid_rows = validation["invalid_rows"]
    invalid_quantity = validation["invalid_quantity"]
    invalid_price = validation["invalid_price"]
    invalid_products = validation["invalid_products"]
    invalid_order_ids = validation["invalid_order_ids"]
    invalid_duplicates = validation["invalid_duplicates"]

    valid_df = df.loc[~invalid_rows].copy()
    valid_df["quantity"] = pd.to_numeric(valid_df["quantity"])
    valid_df["price"] = pd.to_numeric(valid_df["price"])
    valid_df["total_price"] = valid_df["quantity"] * valid_df["price"]

    invalid_df = df.loc[invalid_rows].copy()

    if invalid_df.empty:
        invalid_df["error_reason"] = pd.Series(dtype="object")
    else:
        invalid_df["error_reason"] = invalid_df.apply(
            get_error_reason,
            axis=1,
            args=(
                invalid_quantity,
                invalid_price,
                invalid_products,
                invalid_duplicates,
                invalid_order_ids,
            ),
        )

    summary = calculate_sales_summary(valid_df)
    total_revenue = summary["total_revenue"]
    average_sale_value = summary["average_sale_value"]
    highest_revenue_product = summary["highest_revenue_product"]
    most_units_sold_product = summary["most_units_sold_product"]

    export_summary = pd.DataFrame({
        "Total Revenue": [total_revenue],
        "Valid Records": [len(valid_df)],
        "Invalid Records": [len(invalid_df)],
        "Average Sale Value": [average_sale_value],
        "Highest Revenue Product": [highest_revenue_product],
        "Most Units Sold Product": [most_units_sold_product],
    })
    export_sales_reports(
        valid_df,
        invalid_df,
        export_summary,
        output_path,
    )

    print(export_summary.to_string(index=False))
    print(
        f"Report complete: {len(valid_df)} valid, "
        f"{len(invalid_df)} invalid, "
        f"total revenue = {total_revenue:.2f}"
    )


def main():
    """Parse command-line arguments and run the sales report."""
    parser = argparse.ArgumentParser(
        description="Create cleaned sales reports from a CSV file."
    )

    parser.add_argument(
        "input_file",
        help="Path to the sales CSV file"
    )

    parser.add_argument(
        "output_folder",
        nargs="?",
        default="output",
        help="Folder for generated reports (default: output)"
    )

    args = parser.parse_args()
    create_sales_report(args.input_file, args.output_folder)


if __name__ == "__main__":
    main()