from pathlib import Path
import pandas as pd
import argparse

def validate_sales_data(df):
   
   
   quantity_numeric = pd.to_numeric(df["quantity"], errors="coerce")

   invalid_quantity = (
                        quantity_numeric.isna()
                        | (quantity_numeric <= 0)
                        | (quantity_numeric % 1 != 0)
                    )

   price_numeric = pd.to_numeric(
                        df["price"], errors="coerce"
                    )

   invalid_price = (
                        (price_numeric <= 0) |
                        price_numeric.isna()
                    )

   product_text = df["product"].astype("string").fillna("")

   invalid_products = product_text.str.strip() == ""
   order_id_text = df["order_id"].astype("string").fillna("")

   invalid_order_ids = order_id_text.str.strip() == ""

   invalid_data = (
                        invalid_quantity
                        | invalid_price
                        | invalid_products
                        | invalid_order_ids
                    )
   valid_candidates = df[~invalid_data]

   duplicate_ids = valid_candidates["order_id"].duplicated(keep="first")
   invalid_duplicates = valid_candidates[duplicate_ids].copy()

   invalid_rows = invalid_data.copy()
   invalid_rows.loc[invalid_duplicates.index] = True

   return {
                    "invalid_rows": invalid_rows,
                    "invalid_quantity": invalid_quantity,
                    "invalid_price": invalid_price,
                    "invalid_products": invalid_products,
                    "invalid_duplicates": invalid_duplicates,
                    "invalid_order_ids": invalid_order_ids
                }


def calculate_sales_summary(valid_df):
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
    reasons = []

    if invalid_quantity.loc[row.name]:
        reasons.append("Invalid quantity")

    if invalid_price.loc[row.name]:
        reasons.append("Invalid price")

    if invalid_products.loc[row.name]:
        reasons.append("Missing product")

    if invalid_order_ids.loc[row.name]:
        reasons.append("Missing order ID")
    

    if row.name in invalid_duplicates.index:
        reasons.append("Duplicate order ID")

    
    return "; ".join(reasons)

def export_sales_reports(valid_df, invalid_df, export_summary, output_path):
    invalid_df.to_csv(output_path / "sales_errors.csv", index=False)
    valid_df.to_csv(output_path / "sales_processed.csv", index=False)
    export_summary.to_csv(output_path / "summary.csv", index=False)



def create_sales_report(input_file, output_folder):
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(
    input_file,
    dtype={"order_id": "string"}
)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_file}'.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: '{input_file}' is empty.")
        return
    if df.empty:
        print(f"Error: '{input_file}' has headers but no sales records.")
        return

    df.columns = df.columns.str.strip()
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
    df["order_id"] = df["order_id"].str.strip()
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
            invalid_order_ids
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
        "Most Units Sold Product": [most_units_sold_product]
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