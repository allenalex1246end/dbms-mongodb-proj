import os
from datetime import datetime

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class SalesApp:
    def __init__(self, uri: str, db_name: str = "sales_db", collection_name: str = "sales") -> None:
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection_name]

    def add_sale(self, product: str, quantity: int, price: float) -> str:
        document = {
            "product": product,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "created_at": datetime.utcnow(),
        }
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def list_sales(self) -> list[dict]:
        sales = []
        for sale in self.collection.find().sort("created_at", -1):
            sale["_id"] = str(sale["_id"])
            sales.append(sale)
        return sales

    def update_price(self, sale_id: str, new_price: float) -> bool:
        sale = self.collection.find_one({"_id": ObjectId(sale_id)})
        if not sale:
            return False

        new_total = sale["quantity"] * new_price
        result = self.collection.update_one(
            {"_id": ObjectId(sale_id)},
            {"$set": {"price": new_price, "total": new_total}},
        )
        return result.modified_count > 0

    def delete_sale(self, sale_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(sale_id)})
        return result.deleted_count > 0


def read_number(prompt: str, value_type: type[int] | type[float]) -> int | float:
    while True:
        raw = input(prompt).strip()
        try:
            return value_type(raw)
        except ValueError:
            print("Invalid number. Try again.")


def print_menu() -> None:
    print("\n--- Sales App (MongoDB + Python) ---")
    print("1. Add sale")
    print("2. List sales")
    print("3. Update sale price")
    print("4. Delete sale")
    print("5. Exit")


def main() -> None:
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    try:
        app = SalesApp(mongo_uri)
        # Quick connectivity check for fast feedback on startup.
        app.client.admin.command("ping")
    except PyMongoError as exc:
        print(f"Could not connect to MongoDB: {exc}")
        return

    while True:
        print_menu()
        choice = input("Choose an option (1-5): ").strip()

        try:
            if choice == "1":
                product = input("Product name: ").strip()
                quantity = read_number("Quantity: ", int)
                price = read_number("Price: ", float)
                sale_id = app.add_sale(product, int(quantity), float(price))
                print(f"Sale added with id: {sale_id}")

            elif choice == "2":
                sales = app.list_sales()
                if not sales:
                    print("No sales found.")
                    continue

                for sale in sales:
                    print(
                        f"ID: {sale['_id']} | Product: {sale['product']} | "
                        f"Qty: {sale['quantity']} | Price: {sale['price']:.2f} | "
                        f"Total: {sale['total']:.2f}"
                    )

            elif choice == "3":
                sale_id = input("Sale ID to update: ").strip()
                new_price = read_number("New price: ", float)
                updated = app.update_price(sale_id, float(new_price))
                print("Updated successfully." if updated else "Sale not found or unchanged.")

            elif choice == "4":
                sale_id = input("Sale ID to delete: ").strip()
                deleted = app.delete_sale(sale_id)
                print("Deleted successfully." if deleted else "Sale not found.")

            elif choice == "5":
                print("Goodbye.")
                break

            else:
                print("Invalid choice.")

        except (PyMongoError, ValueError) as exc:
            print(f"Operation failed: {exc}")


if __name__ == "__main__":
    main()
