import pandas as pd

df = pd.read_csv("sales_processed.csv")

print(df.head())
print("Number of valid sales:", len(df))
print("Total revenue:", df["total"].sum())
highest_sale =df.loc[df["total"].idxmax()]
print("Highest sale:", highest_sale["order_id"], "with total:", highest_sale["total"])
revenue_by_product = df.groupby("product")["total"].sum()

print(revenue_by_product.sort_values(ascending=False))
print("Sum of product revenues:", revenue_by_product.sum())

df["calculated_total"] = df["quantity"] * df["price"]

df["difference"] = df["total"] - df["calculated_total"]

print(df[df["difference"] != 0])