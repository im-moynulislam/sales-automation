# Sales Automation

A Python-based sales data processing and reporting tool that reads sales records from CSV files, validates data, identifies invalid and duplicate records, and generates clean sales reports.

This project demonstrates practical Python skills in CSV processing, data validation, error handling, data analysis, report generation, and automated testing.

## Features

- Reads sales data from CSV files using Pandas.
- Validates required columns and individual sales records.
- Detects missing product names.
- Identifies invalid quantities, including zero, negative, fractional, missing, and non-numeric values.
- Identifies invalid prices, including zero, negative, missing, and non-numeric values.
- Detects duplicate order IDs among otherwise valid records.
- Keeps the first valid record when duplicate order IDs occur.
- Separates valid sales records from invalid records.
- Calculates total revenue and average sale value.
- Identifies the highest-revenue product.
- Identifies the product with the most units sold.
- Exports processed sales data, validation errors, and summary reports as CSV files.
- Includes an automated test suite using pytest.

## Technologies Used

- **Python** — Main programming language.
- **Pandas** — CSV processing and data manipulation.
- **NumPy** — Numerical operations.
- **pytest** — Automated testing.

## Project Requirements

You need Python installed on your computer to run this project.

Install the required dependencies using:

```bash
python -m pip install -r requirements.txt
```

## Project Structure

```text
sales-automation/
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

| File | Description |
|---|---|
| `sales_report.py` | Main program for processing sales data and generating reports. |
| `tests/test_sales_report.py` | Automated tests for validation, error handling, and report generation. |
| `requirements.txt` | Lists the required Python packages. |
| `sales_automation_test_60_rows.csv` | Sample sales dataset for testing the program. |
| `.gitignore` | Specifies files and folders Git should ignore. |
| `README.md` | Project documentation. |

## Expected Input Format

The program expects a CSV file containing these required columns:

| Column | Description | Example |
|---|---|---|
| `order_id` | Identifier for each order | `5001` |
| `product` | Name of the product | `Notebook` |
| `quantity` | Number of units sold | `2` |
| `price` | Price per unit | `50` |

### Example Input

```csv
order_id,product,quantity,price
5001,Notebook,2,50
5002,Pen,5,10
5003,Pencil,10,5
5004,School Bag,1,850
5005,Ruler,3,20
```

## How to Run

Open a terminal in the project directory.

Run the program with an input CSV file and an output directory:

```bash
python sales_report.py "sales.csv" "output"
```

Replace `sales.csv` with the path to your input file.

The second argument specifies where the generated reports will be saved. If it is omitted, the program uses the default output folder configured in the script.

For example, to run the included sample dataset:

```bash
python sales_report.py "sales_automation_test_60_rows.csv" "output"
```

## Data Validation and Duplicate Handling

The program follows a validation-first approach when processing sales records.

### 1. Record Validation

Each record is checked for invalid or missing data.

Examples include:

- Missing product names.
- Missing quantities or prices.
- Zero or negative quantities.
- Fractional quantities.
- Non-numeric quantities or prices.
- Zero or negative prices.

Records that fail validation are placed in the error report with the corresponding reason.

### 2. Duplicate Order Detection

Duplicate detection happens after individual record validation.

The program follows a **first-valid-record-wins** rule:

- Invalid records are rejected and do not reserve their order IDs.
- The first valid record with an order ID is accepted.
- A later valid record with the same order ID is rejected as a duplicate.
- An invalid record with an order ID does not prevent a later valid record from being accepted.

This approach ensures that duplicate detection is applied only to otherwise valid sales records.

## Generated Reports

After successful processing, the program generates three CSV reports in the output directory.

| Report | Description |
|---|---|
| `sales_processed.csv` | Contains validated and cleaned sales records, including calculated total prices. |
| `sales_errors.csv` | Contains invalid and duplicate records with their corresponding error reasons. |
| `summary.csv` | Contains overall sales statistics and product performance information. |

### 1. Processed Sales Report

Contains the accepted sales records.

Example:

| order_id | product | quantity | price | total_price |
|---|---|---:|---:|---:|
| 5001 | Notebook | 2 | 50 | 100 |
| 5002 | Pen | 5 | 10 | 50 |
| 5003 | Pencil | 10 | 5 | 50 |

### 2. Error Report

Contains records rejected during validation or duplicate detection, along with the reason for rejection.

Example:

| order_id | product | quantity | price | error_reason |
|---|---|---:|---:|---|
| 5041 | Bad Zero Quantity | 0 | 20 | Invalid quantity |
| 5046 | Bad Zero Price | 2 | 0 | Invalid price |
| 5050 | | 2 | 20 | Missing product |
| 5001 | Duplicate Notebook | 3 | 55 | Duplicate order ID |

A record can contain more than one validation error.

### 3. Sales Summary Report

Provides an overview of the processed sales data, including:

- Total revenue.
- Number of valid records.
- Number of invalid records.
- Average sale value.
- Highest-revenue product.
- Product with the most units sold.

### Example Results

The following figures are from a sample execution of the project:

| Metric | Result |
|---|---:|
| Total Revenue | 13,040 |
| Valid Records | 48 |
| Invalid Records | 15 |
| Average Sale Value | 271.67 |
| Highest Revenue Product | School Bag |
| Most Units Sold Product | Pencil |

These figures are illustrative results from the included sample dataset, not fixed values produced by every execution.

## Running Automated Tests

This project uses pytest to test its functionality.

Run the complete test suite:

```bash
python -m pytest -v
```

The test suite covers:

- Sales data validation.
- Invalid and duplicate records.
- Missing columns and empty files.
- CSV reading and error handling.
- Report generation.
- Summary calculations.
- Command-line execution.

### Latest Test Result

**125 tests passed.**

The test suite helps verify that the program behaves as expected across normal and invalid input scenarios.

## Project Purpose

This project was developed as a practical Python learning exercise to strengthen my understanding of:

- Python programming and functions.
- Working with CSV files.
- Data processing with Pandas and NumPy.
- Data validation and error handling.
- Generating automated reports.
- Writing and running automated tests with pytest.
- Organizing and documenting a Python project.
- Using Git and GitHub for version control.

The project was developed incrementally, with testing and improvements throughout the process.

## Future Improvements

Possible future enhancements include:

- Excel file support.
- More customizable report formats.
- Additional sales analytics.
- Configurable validation rules.

These are potential future improvements and are not currently included in the project.

---

**Project:** Sales Automation  
**Language:** Python  
**Testing:** pytest  
**Status:** Completed learning project
