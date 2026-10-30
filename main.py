import csv
import math

def calculate_total(quantity, price):
    total = quantity * price
    return total


def validate_quantity(value):
    value = value.strip()

    try:
        quantity = int(value)
    except ValueError:
        try:
            float(value)
            # Numeric, but not accepted by int()
            business_message = "Quantity must be a whole number. Received: " + value
            return None, business_message
        except ValueError:
            # Not numeric
            business_message = "Quantity must be a number. Received: " + value
            return None, business_message

    # Check whether quantity is positive.
    if quantity <= 0:
        business_message = "Quantity must be greater than zero. Received: " + str(quantity)
        return None, business_message

    return quantity, None
def validate_price(value):



    value = value.strip()
    try:
        price = float(value)
    
    except ValueError:
            # Not numeric
            business_message = "Price must be a number. Received: " + value
            return None, business_message

    # Check whether price is positive.
    if not math.isfinite(price):
        business_message = "Price must be a finite number. Received: " + str(price)
        return None, business_message
    if price <= 0:
        business_message = "Price must be greater than zero. Received: " + str(price)
        return None, business_message

    return price, None
 # test_price_values = ["10.5", "-5", "abc", "0", "100", "NaN", "inf", "-inf", "1e3"]


def validate_product(value):
    # Your code here
    value = value.strip()
    if not value:
        return None,"Product name cannot be empty."
    return value, None

def validate_order_id(value):
    # Your code here
    value = value.strip()
    try:
        order_id = int(value)
        if order_id <= 0:
            return None, "Order ID must be a positive integer."
        return value, None
    except ValueError:
        return None, "Order ID must be a number."

def process_sale(sale,seen_order_ids):

    original_order_id = sale["order_id"]
    order_id, business_message = validate_order_id(original_order_id)
    
    if business_message:
        error_record = {
                "order_id": original_order_id,
                "business_message": business_message,
                "technical_message": ""
            }
        return None, error_record
    
    original_quantity = sale["quantity"]
    quantity, business_message = validate_quantity(original_quantity)

    if business_message:
        error_record = {
            "order_id": sale["order_id"],
            "business_message": business_message,
            "technical_message": ""
        }
        return None, error_record

    original_price = sale["price"]
    price, business_message = validate_price(original_price)

    if business_message:
        error_record = {
            "order_id": sale["order_id"],
            "business_message": business_message,
            "technical_message": ""
        }
        return None, error_record

    original_product = sale["product"]
    product, business_message = validate_product(original_product)

    if business_message:
        error_record = {
            "order_id": sale["order_id"],
            "business_message": business_message,
            "technical_message": ""
        }
        return None, error_record

    
    if order_id in seen_order_ids:
        error_record = {
            "order_id": order_id,
            "business_message": "Duplicate order ID",
            "technical_message": ""
        }
        return None, error_record
    print(f"Checking ID: {order_id}, Seen IDs: {seen_order_ids}")

    seen_order_ids.add(order_id)
    print(f"Added ID: {order_id}, Seen IDs now: {seen_order_ids}")
    total = calculate_total(quantity, price)
    
    processed_sale = {
        "order_id": order_id,
        "product": product,
        "quantity": quantity,
        "price": price,
        "total": total
    }

    return processed_sale, None
# seen_order_ids = set()


with open("sales.csv", "r", newline="", encoding="utf-8") as file:
    # print("Reading sales.csv")
    reader = csv.DictReader(file)
    print(reader.fieldnames)
    required_columns = {
    "order_id",
    "product",
    "quantity",
    "price"
}
    
    missing_columns = required_columns - set(reader.fieldnames or [])

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
    )


    #print(first_row)
    #print(f"Product: {first_row['product']}, Quantity: {first_row['quantity']}")
    fieldnames = ["order_id", "product", "quantity", "price", "total"]

    with open("sales_processed.csv", "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        total_revenue = 0
        seen_order_ids = set()
        error_rows = []
        for sale in reader:
            
            processed_sale, error_record = process_sale(sale, seen_order_ids)

            if error_record:
                error_rows.append(error_record)
                continue

            total_revenue += processed_sale["total"]

            print(
                    f"Product: {processed_sale['product']}, "
                    f"Quantity: {processed_sale['quantity']}, "
                    f"Total: {processed_sale['total']}"
                )

            writer.writerow(processed_sale)
        Error_fieldnames = ["order_id", "business_message", "technical_message"]
        with open("sales_errors.csv", "w", newline="", encoding="utf-8") as error_file:
            writer = csv.DictWriter(error_file, fieldnames=Error_fieldnames)
            writer.writeheader()
            
            for error_row in error_rows:
                writer.writerow(error_row)
                  
        print(f"Total revenue: {total_revenue}")
        if error_rows:
            print("Error rows:")
            for row in error_rows:
                print(row)