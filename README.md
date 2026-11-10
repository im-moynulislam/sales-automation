# Sales Automation

A Python project that processes sales data from CSV files, validates records, separates valid and invalid data, and generates sales summary reports.

## Features

- Reads sales data from CSV files.
- Validates required columns and sales records.
- Identifies invalid quantities, prices, and missing product names.
- Detects duplicate order IDs among otherwise valid records.
- Separates valid records from invalid records.
- Calculates total revenue and average sale value.
- Identifies the top-performing products by revenue and units sold.
- Exports cleaned sales data, validation errors, and summary reports as CSV files.

## Requirements

- Python
- pandas
- NumPy
- pytest (for running automated tests)

Install the project dependencies using:

```bash
python -m pip install -r requirements.txt
```

## How to Run

Open a terminal in the project directory and run:

```bash
python sales_report.py "sales.csv" "output"
```

Replace `sales.csv` with the path to your input CSV file.

The second argument specifies the output folder. If omitted, the program uses the default output folder configured in the script.

## Expected Input

The input CSV file should contain the following columns:

| Column | Description |
|---|---|
| `order_id` | Unique identifier for each order |
| `product` | Name of the product |
| `quantity` | Number of units sold |
| `price` | Price per unit |

## Generated Reports

The program generates three CSV reports:

| File | Description |
|---|---|
| `sales_processed.csv` | Validated and cleaned sales records |
| `sales_errors.csv` | Invalid records with their corresponding error reasons |
| `summary.csv` | Overall sales statistics and product performance information |

All reports are saved in the specified output folder.

## Running Tests

This project uses pytest for automated testing.

To run the complete test suite, execute:

```bash
python -m pytest -v
```

The current test suite contains 125 tests covering:

- Sales data validation
- Invalid and duplicate records
- Missing columns and empty files
- CSV reading and error handling
- Report generation
- Summary calculations
- Command-line execution

**Latest test result:** 125 tests passed.

## Project Structure

```text
sales_automation/
│
├── tests/
│   └── test_sales_report.py
│
├── .gitignore
├── README.md
├── requirements.txt
├── sales_automation_test_60_rows.csv
└── sales_report.py
```

### Main Files

- `sales_report.py` — Main sales data processing and reporting program.
- `tests/test_sales_report.py` — Automated tests for validation, error handling, and report generation.
- `requirements.txt` — Lists the project dependencies.
- `sales_automation_test_60_rows.csv` — Sample sales dataset for testing.
- `.gitignore` — Specifies files and folders Git should ignore.
- `README.md` — Project documentation.

## Project Status

This project started as a Python learning exercise and has been developed incrementally.

It currently includes CSV processing, data validation, error handling, automated testing, and report generation.

Git and GitHub are used for version control and project storage.

Future improvements may include additional reporting features and batch processing.