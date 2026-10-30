# Sales Automation

A Python project that processes sales data from CSV files and generates cleaned data, validation-error reports, and a sales summary.

## Features

- Reads sales data from a CSV file.
- Validates required columns and sales records.
- Identifies invalid quantities, prices, and missing product names.
- Detects duplicate order IDs among otherwise valid records.
- Separates valid records from invalid records.
- Calculates total revenue and average sale value.
- Summarizes revenue and units sold by product.
- Generates CSV reports.

## Requirements

- Python
- pandas

Install pandas with:

```bash
python -m pip install pandas
```

## How to Run

Open a terminal in the project folder and run:

```bash
python sales_report.py "sales.csv" "output"
```

Replace `sales.csv` with the path to your input CSV file.

The second argument specifies the output folder. If omitted, the program uses the default output folder configured in the script.

## Expected Input

The input CSV should contain these columns:

- `order_id`
- `product`
- `quantity`
- `price`

## Generated Reports

The program generates reports such as:

- `sales_processed.csv` — valid, cleaned sales records.
- `sales_errors.csv` — invalid records and their error reasons.
- `summary.csv` — overall sales statistics.

The exact output location depends on the output folder supplied when running the program.

## Project Files

- `sales_report.py` — main sales automation program.
- `main.py` — earlier Python implementation.
- `sales_summary.py` — earlier Python implementation.
- `pandas_intro.py` — Pandas learning file.
- `sales_automation_test_60_rows.csv` — test dataset.
- `.gitignore` — files and folders Git should ignore.

## Current Status

This is a learning and development project. The program is being improved incrementally, with testing and error handling used to make it more reliable.
This project is maintained using Git for version control and GitHub for remote storage.
Future improvements will include automated tests and batch processing.
