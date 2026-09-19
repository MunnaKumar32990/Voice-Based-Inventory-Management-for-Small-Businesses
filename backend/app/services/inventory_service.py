from motor.motor_asyncio import AsyncIOMotorDatabase
from decimal import Decimal
from datetime import datetime, timezone
from app.services.unit_service import UnitService
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.balance_repo import BalanceRepository
from app.repositories.alert_repo import AlertRepository
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError


def _safe_oid(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError, ValueError):
        return None


def _product_name(product: dict) -> str:
    return product.get("display_name") or product.get("name") or "product"


class InventoryService:
    def __init__(self):
        self.unit_service = UnitService()
        self.txn_repo = TransactionRepository()
        self.balance_repo = BalanceRepository()
        self.alert_repo = AlertRepository()

    async def prepare_transaction(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, operation: str, quantity: Decimal, unit: str):
        oid = _safe_oid(product_id)
        product = None
        if oid is not None:
            product = await db.products.find_one({"_id": oid, "shop_id": shop_id})
        if not product:
            product = await db.products.find_one({"_id": str(product_id), "shop_id": shop_id})
        if not product: raise ValueError("Product not found")

        norm_unit = self.unit_service.normalize_unit(unit)
        if not self.unit_service.is_valid_unit(product, norm_unit):
            raise ValueError(f"Invalid unit {unit} for {_product_name(product)}")

        base_qty, base_unit = self.unit_service.convert_to_base_unit(product, quantity, norm_unit)
        balance = await self.balance_repo.find_by_product(db, shop_id, str(product["_id"]))
        current_qty = Decimal(str(balance["quantity"])) if balance else Decimal(0)

        if operation == "STOCK_OUT" and current_qty < base_qty:
            raise ValueError(f"Insufficient stock. Have {current_qty} {base_unit}, need {base_qty}")

        if operation == "STOCK_IN":
            new_qty = current_qty + base_qty
        elif operation == "STOCK_OUT":
            new_qty = current_qty - base_qty
        elif operation == "ADJUSTMENT":
            # ADJUSTMENT sets absolute stock level to the given quantity
            new_qty = base_qty
        else:
            raise ValueError(f"Unsupported operation {operation}")

        return {
            "product_name": _product_name(product),
            "operation": operation,
            "quantity": float(quantity),
            "unit": norm_unit,
            "base_quantity": float(base_qty),
            "base_unit": base_unit,
            "current_balance": float(current_qty),
            "new_balance": float(new_qty)
        }

    async def commit_transaction(self, db: AsyncIOMotorDatabase, shop_id: str, user_id: str, product_id: str, operation: str, quantity: Decimal, unit: str, reason: str, source: str, idempotency_key: str, price_total: Decimal = None, interaction_id: str = None):
        existing_txn = await self.txn_repo.find_by_idempotency_key(db, shop_id, idempotency_key)
        if existing_txn:
            return {"status": "already_processed", "transaction_id": str(existing_txn["_id"]),
                    "new_balance": existing_txn.get("new_balance"),
                    "balance_unit": existing_txn.get("base_unit")}

        try:
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    return await self._do_commit(
                        db, shop_id, user_id, product_id, operation, quantity, unit,
                        reason, source, idempotency_key, price_total, interaction_id, session=session
                    )
        except DuplicateKeyError:
            # Concurrent retry with same idempotency key — return original
            existing_txn = await self.txn_repo.find_by_idempotency_key(db, shop_id, idempotency_key)
            if existing_txn:
                return {"status": "already_processed", "transaction_id": str(existing_txn["_id"])}
            raise ValueError("Duplicate request detected")
        except Exception as e:
            msg = str(e).lower()
            if "replica set" in msg or "standalone" in msg or "transaction numbers" in msg or "sessions are not supported" in msg:
                # Fallback for standalone MongoDB local dev
                try:
                    return await self._do_commit(
                        db, shop_id, user_id, product_id, operation, quantity, unit,
                        reason, source, idempotency_key, price_total, interaction_id, session=None
                    )
                except DuplicateKeyError:
                    existing_txn = await self.txn_repo.find_by_idempotency_key(db, shop_id, idempotency_key)
                    if existing_txn:
                        return {"status": "already_processed", "transaction_id": str(existing_txn["_id"])}
                    raise ValueError("Duplicate request detected")
            raise

    async def _do_commit(self, db: AsyncIOMotorDatabase, shop_id: str, user_id: str, product_id: str, operation: str, quantity: Decimal, unit: str, reason: str, source: str, idempotency_key: str, price_total: Decimal = None, interaction_id: str = None, session=None):
        if operation not in ("STOCK_IN", "STOCK_OUT", "ADJUSTMENT"):
            raise ValueError(f"Unsupported operation {operation}")
        oid = _safe_oid(product_id)
        product = None
        if oid is not None:
            product = await db.products.find_one({"_id": oid, "shop_id": shop_id}, session=session)
        if not product:
            product = await db.products.find_one({"_id": str(product_id), "shop_id": shop_id}, session=session)
        if not product:
            raise ValueError("Product not found")
        canonical_pid = str(product["_id"])

        norm_unit = self.unit_service.normalize_unit(unit)
        base_qty, base_unit = self.unit_service.convert_to_base_unit(product, quantity, norm_unit)

        balance = await self.balance_repo.find_by_product(db, shop_id, canonical_pid, session=session)
        current_qty = Decimal(str(balance["quantity"])) if balance else Decimal(0)

        if operation == "STOCK_OUT" and current_qty < base_qty:
            raise ValueError(f"Insufficient stock. Available: {current_qty} {base_unit}, requested: {base_qty} {base_unit}")

        if operation == "STOCK_IN":
            new_qty = current_qty + base_qty
        elif operation == "STOCK_OUT":
            new_qty = current_qty - base_qty
        else:  # ADJUSTMENT sets absolute level
            new_qty = base_qty

        txn_doc = {
            "shop_id": shop_id,
            "product_id": canonical_pid,
            "user_id": user_id,
            "operation": operation,
            "quantity": float(quantity),
            "unit": norm_unit,
            "base_quantity": float(base_qty),
            "base_unit": base_unit,
            "new_balance": float(new_qty),
            "reason": reason,
            "source": source,
            "idempotency_key": idempotency_key,
            "price_total": float(price_total) if price_total else None,
            "interaction_id": interaction_id,
            "timestamp": datetime.now(timezone.utc)
        }
        txn_id = await self.txn_repo.insert(db, txn_doc, session=session)

        await self.balance_repo.upsert(db, shop_id, canonical_pid, new_qty, base_unit, session=session)

        threshold = product.get("reorder_threshold", product.get("low_stock_threshold", 0))
        if new_qty <= threshold:
            await self.alert_repo.upsert_low_stock(db, shop_id, canonical_pid, float(new_qty), float(threshold), session=session)
        else:
            await self.alert_repo.resolve(db, shop_id, canonical_pid, session=session)

        return {"status": "success", "transaction_id": txn_id, "new_balance": float(new_qty), "balance_unit": base_unit}

    async def get_dashboard_summary(self, db: AsyncIOMotorDatabase, shop_id: str):
        in_count = await self.txn_repo.count_today(db, shop_id, "STOCK_IN")
        out_count = await self.txn_repo.count_today(db, shop_id, "STOCK_OUT")
        alerts = await self.alert_repo.count_open(db, shop_id)
        return {
            "today_stock_in": in_count,
            "today_stock_out": out_count,
            "open_alerts": alerts
        }

    async def get_stock_answer(self, db: AsyncIOMotorDatabase, shop_id: str, product_text: str):
        return f"Stock info for {product_text}"

    async def get_low_stock_items(self, db: AsyncIOMotorDatabase, shop_id: str):
        return await self.balance_repo.find_low_stock(db, shop_id)
