from pathlib import Path
import pandas as pd
import argparse


def create_sales_report(input_file, output_folder):
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: '{input_file}' is empty.")
        return
    if df.empty:
            print(f"Error: '{input_file}' has headers but no sales records.")
            return


    required_columns = {
        "order_id",
        "product",
        "quantity",
        "price"
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        print(f"Error: Missing required columns: {sorted(missing_columns)}")
        return

    
    quantity_numeric = pd.to_numeric(df["quantity"], errors="coerce")

    invalid_quantity = (
        quantity_numeric.isna()
        | (quantity_numeric <= 0)
        | (quantity_numeric % 1 != 0)
    )
    # print(df[invalid_quantity])
    # print("Invalid or missing quantities:", invalid_quantity.sum())

    price_numeric = pd.to_numeric(
        df["price"], errors="coerce"
    )

    invalid_price = (
        (price_numeric <= 0) |
        price_numeric.isna()
    )

    # print("Invalid or missing prices:", invalid_price.sum())


    invalid_products = df["product"].isna() | (df["product"].str.strip() == "")
    # print("Invalid products:", invalid_products.sum())

    invalid_data = (
        invalid_quantity
        | invalid_price
        | invalid_products
    )
    valid_candidates = df[~invalid_data]



    duplicate_ids = valid_candidates["order_id"].duplicated(keep="first")
    invalid_duplicates = valid_candidates[duplicate_ids].copy()
    # print("Duplicate rows:", duplicate_ids.sum())

    # invalid_rows = invalid_quantity | invalid_price | invalid_products | duplicate_ids

    invalid_rows = invalid_data.copy()

    invalid_rows.loc[invalid_duplicates.index] = True


    invalid_candidates = df[invalid_data]
    # print("Valid candidates:", len(valid_candidates))

    print("Total rows:", len(df))
    print("Invalid data rows:", int(invalid_data.sum()))
    print("Duplicate valid IDs:", int(duplicate_ids.sum()))
    print("Invalid rows:", int(invalid_rows.sum()))


    valid_df = df.loc[~invalid_rows].copy()
    valid_df["quantity"] = pd.to_numeric(valid_df["quantity"])
    valid_df["price"] = pd.to_numeric(valid_df["price"])
    valid_df["total_price"] = valid_df["quantity"] * valid_df["price"]

    invalid_df = df.loc[invalid_rows].copy()

    def get_error_reason(row):
        reasons = []

        if invalid_quantity.loc[row.name]:
            reasons.append("Invalid quantity")

        if invalid_price.loc[row.name]:
            reasons.append("Invalid price")

        if invalid_products.loc[row.name]:
            reasons.append("Missing product")

        if row.name in invalid_duplicates.index:
            reasons.append("Duplicate order ID")

        return "; ".join(reasons)


    if invalid_df.empty:
        invalid_df["error_reason"] = pd.Series(dtype="object")
    else:
        invalid_df["error_reason"] = invalid_df.apply(
            get_error_reason, axis=1
        )

        
    # print("Invalid DataFrame shape:", invalid_df.shape)
    # print("Invalid DataFrame columns:", invalid_df.columns.tolist())
    # print("Duplicate columns:", invalid_df.columns[invalid_df.columns.duplicated()].tolist())
    # print("Result type:", type(result))
    # print(result)

    # print("Result type:", type(result))
    # print(result)

    # invalid_df["error_reason"] = result

    invalid_df.to_csv(output_path / "sales_errors.csv", index=False)

    valid_df.to_csv(output_path / "sales_processed.csv", index=False)




    processed_check = pd.read_csv(output_path / "sales_processed.csv")
    errors_check = pd.read_csv(output_path / "sales_errors.csv")


    total_revenue = valid_df["total_price"].sum()


    revenue_by_product = (
        valid_df.groupby("product")["total_price"]
        .sum()
        .sort_values(ascending=False)
    )


    units_by_product = (
        valid_df.groupby("product")["quantity"]
        .sum().sort_values(ascending=False)
        # Sum quantities and sort from highest to lowest
    )

    average_sale_value = (
    total_revenue / len(valid_df)
    if not valid_df.empty
    else 0
)
    # print("Average sale value:", average_sale_value)

    if valid_df.empty:
        highest_revenue_product = "N/A"
        most_units_sold_product = "N/A"
    else:
        highest_revenue_product = revenue_by_product.idxmax()
        most_units_sold_product = units_by_product.idxmax()


    print("Valid DataFrame empty:", valid_df.empty)
    print("Highest revenue product:", repr(highest_revenue_product))
    print("Most units sold product:", repr(most_units_sold_product))


   
    export_summary = pd.DataFrame({
        "Total Revenue": [total_revenue],
        "Valid Records": [len(valid_df)],
        "Invalid Records": [len(invalid_df)],
        "Average Sale Value": [average_sale_value],
        "Highest Revenue Product": [highest_revenue_product],
        "Most Units Sold Product": [most_units_sold_product]
    })
    print("Summary columns:", export_summary.columns.tolist())
    print("Highest revenue value:", repr(export_summary.loc[0, "Highest Revenue Product"]))
    print("Most units value:", repr(export_summary.loc[0, "Most Units Sold Product"]))
    print(export_summary.to_string(index=False))

    export_summary.to_csv(output_path / "summary.csv", index=False)

    summary_check = pd.read_csv(output_path / "summary.csv", keep_default_na=False)
    print(summary_check)


        # Move your completed Pandas workflow here.
        # Export files using output_path / "filename.csv"
    processed_check = pd.read_csv(output_path / "sales_processed.csv")

    print(
        f"Report complete: {len(valid_df)} valid, "
        f"{len(invalid_df)} invalid, "
        f"total revenue = {total_revenue:.2f}"
    )
if __name__ == "__main__":
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