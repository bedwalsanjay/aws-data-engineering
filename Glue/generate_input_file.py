import csv
import random
from datetime import datetime, timedelta

def generate_orders_csv(file_path, num_records=100):

    customer_names = [
        "john smith", "jane doe", "robert brown", "emily davis",
        "michael wilson", "sarah johnson", "david lee", "lisa anderson",
        "james taylor", "mary thomas"
    ]

    products = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headphones", "Webcam"]

    start_date = datetime(2024, 1, 1)

    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(["order_id", "customer_name", "product", "amount", "order_date"])

        # Records
        for i in range(1, num_records + 1):
            order_id = f"ORD-{i:04d}"
            customer_name = random.choice(customer_names)
            product = random.choice(products)
            amount = round(random.uniform(10.0, 2000.0), 2)
            order_date = (start_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')

            writer.writerow([order_id, customer_name, product, amount, order_date])

        # Add a few duplicate records to demonstrate dropDuplicates
        writer.writerow(["ORD-0001", "john smith", "Laptop", 999.99, "2024-01-01"])
        writer.writerow(["ORD-0002", "jane doe", "Phone", 599.99, "2024-01-02"])

        # Add a few records with invalid amount to demonstrate filter
        writer.writerow([f"ORD-{num_records + 1:04d}", "test user", "Tablet", -50.0, "2024-03-01"])
        writer.writerow([f"ORD-{num_records + 2:04d}", "test user", "Monitor", 0, "2024-03-02"])

    print(f"Generated {num_records + 4} records at {file_path}")
    print(f"  - {num_records} normal records")
    print(f"  - 2 duplicate records (ORD-0001, ORD-0002)")
    print(f"  - 2 invalid amount records (negative and zero)")


if __name__ == '__main__':
    generate_orders_csv('orders.csv', num_records=100)
