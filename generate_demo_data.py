import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "data" / "retail_sales_demo.csv"

HEADERS = [
    "Order_Date",
    "Customer_ID",
    "Region",
    "Category",
    "Product",
    "Quantity",
    "Unit_Price",
    "Sales"
]

ROWS = [
    ["2026-01-02", "C001", "North", "Electronics", "Laptop Bag", 2, 1200, 2400],
    ["2026-01-03", "C002", "South", "electronics ", "Keyboard", 3, 800, 2400],
    ["2026-01-04", "C003", "West", "Furniture", "Chair", 1, 2500, 2500],
    ["2026-01-05", "C004", "East", "Grocery", "Coffee", 5, 300, 1500],
    ["2026-01-06", "C005", "North", "Electronics", "Mouse", 4, 450, 1800],
    ["2026-01-07", "C006", "South", "Furniture", "Table", 1, 5500, 5500],
    ["2026-01-08", "", "West", "Grocery", "Tea", 4, 250, 1000],
    ["2026-01-09", "C008", "East", "Electronics", "Monitor", 2, 9000, 18000],
    ["not-a-date", "C009", "North", "Electronics", "Headset", 2, 1500, 3000],
    ["2026-01-11", "C010", "South", "Grocery", "Sugar", -2, 60, -120],
    ["2026-01-12", "C011", "West", "Furniture", "Desk", 1, 7000, 6800],
    ["2026-01-13", "C012", "East", "electronics", "USB Cable", 5, 200, 1000],
    ["2026-01-14", "C013", "North", "Grocery", "Rice", 2, 700, 1400],
    ["2026-01-15", "C014", "South", "Furniture", "Chair", 2, 2500, 5000],
    ["2026-01-16", "C015", "West", "Electronics", "Webcam", 1, 2200, 2200],
]


def create_demo_dataset():
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    rows = ROWS.copy()
    rows.append(rows[0].copy())

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(HEADERS)
        writer.writerows(rows)

    print(
        f"Demo dataset created successfully:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    create_demo_dataset()