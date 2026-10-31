import pandas as pd

df = pd.read_csv("sales.csv")


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

invalid_rows = invalid_quantity | invalid_price | invalid_products | duplicate_ids




invalid_candidates = df[invalid_data]




valid_df = df[~invalid_rows]
valid_df["quantity"] = pd.to_numeric(valid_df["quantity"])
valid_df["price"] = pd.to_numeric(valid_df["price"])
valid_df["total_price"] = valid_df["quantity"] * valid_df["price"]

invalid_df = df[invalid_rows]

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


invalid_df["error_reason"] = invalid_df.apply(
    get_error_reason, axis=1
)

invalid_df.to_csv(output_path / "sales_errors.csv", index=False)


#
export_valid_df = valid_df.to_csv(output_path / "sales_processed.csv", index=False)



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

average_sale_value = valid_df["total_price"].mean()
# print("Average sale value:", average_sale_value)
export_summary = pd.DataFrame({
    "Total Revenue": [total_revenue],
    "Valid Records": [len(processed_check)],
    "Invalid Records": [len(errors_check)],
    "Average Sale Value": [round(average_sale_value, 2)],
    "Highest Revenue Product": [revenue_by_product.idxmax()],
    "Most Units Sold Product": [units_by_product.idxmax()]
})

export_summary.to_csv("summary.csv", index=False)

summary_check = pd.read_csv("summary.csv")
# print(summary_check)