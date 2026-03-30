import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class SalesService:
    def __init__(self, uri: str, db_name: str = "sales_db", collection_name: str = "sales") -> None:
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection_name]

    def add_sale(self, product: str, quantity: int, price: float) -> str:
        now = datetime.now(timezone.utc)
        document = {
            "product": product,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "created_at": now,
            "updated_at": now,
        }
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def list_sales(self) -> list[dict]:
        sales = []
        for sale in self.collection.find().sort("created_at", -1):
            sales.append(self._serialize_sale(sale))
        return sales

    def update_sale(self, sale_id: str, product: str, quantity: int, price: float) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(sale_id)},
            {
                "$set": {
                    "product": product,
                    "quantity": quantity,
                    "price": price,
                    "total": quantity * price,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.matched_count > 0

    def delete_sale(self, sale_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(sale_id)})
        return result.deleted_count > 0

    @staticmethod
    def _serialize_sale(sale: dict) -> dict:
        created_at = sale.get("created_at")
        updated_at = sale.get("updated_at")
        return {
            "id": str(sale["_id"]),
            "product": sale.get("product", ""),
            "quantity": int(sale.get("quantity", 0)),
            "price": float(sale.get("price", 0)),
            "total": float(sale.get("total", 0)),
            "created_at": created_at.isoformat() if isinstance(created_at, datetime) else None,
            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else None,
        }


def validate_sale_payload(payload: dict) -> tuple[str, int, float]:
    product = str(payload.get("product", "")).strip()
    if not product:
        raise ValueError("Product is required.")

    try:
        quantity = int(payload.get("quantity", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be an integer.") from exc

    try:
        price = float(payload.get("price", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Price must be a number.") from exc

    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    if price <= 0:
        raise ValueError("Price must be greater than 0.")

    return product, quantity, price


def create_app() -> Flask:
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "sales_db")
    collection_name = os.getenv("MONGODB_COLLECTION", "sales")

    service = SalesService(mongo_uri, db_name, collection_name)

    app = Flask(__name__)

    try:
        service.client.admin.command("ping")
    except PyMongoError as exc:
        app.logger.warning("MongoDB ping failed during startup: %s", exc)

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/health")
    def health() -> tuple:
        try:
            service.client.admin.command("ping")
            return jsonify({"status": "ok"}), 200
        except PyMongoError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.get("/api/sales")
    def get_sales() -> tuple:
        try:
            sales = service.list_sales()
            return jsonify(sales), 200
        except PyMongoError as exc:
            return jsonify({"error": f"Failed to fetch sales: {exc}"}), 500

    @app.post("/api/sales")
    def create_sale() -> tuple:
        payload = request.get_json(silent=True) or {}
        try:
            product, quantity, price = validate_sale_payload(payload)
            sale_id = service.add_sale(product, quantity, price)
            return jsonify({"message": "Sale created.", "id": sale_id}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except PyMongoError as exc:
            return jsonify({"error": f"Failed to create sale: {exc}"}), 500

    @app.put("/api/sales/<sale_id>")
    def update_sale(sale_id: str) -> tuple:
        payload = request.get_json(silent=True) or {}
        try:
            product, quantity, price = validate_sale_payload(payload)
            updated = service.update_sale(sale_id, product, quantity, price)
            if not updated:
                return jsonify({"error": "Sale not found."}), 404
            return jsonify({"message": "Sale updated."}), 200
        except InvalidId:
            return jsonify({"error": "Invalid sale id."}), 400
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except PyMongoError as exc:
            return jsonify({"error": f"Failed to update sale: {exc}"}), 500

    @app.delete("/api/sales/<sale_id>")
    def delete_sale(sale_id: str) -> tuple:
        try:
            deleted = service.delete_sale(sale_id)
            if not deleted:
                return jsonify({"error": "Sale not found."}), 404
            return jsonify({"message": "Sale deleted."}), 200
        except InvalidId:
            return jsonify({"error": "Invalid sale id."}), 400
        except PyMongoError as exc:
            return jsonify({"error": f"Failed to delete sale: {exc}"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
