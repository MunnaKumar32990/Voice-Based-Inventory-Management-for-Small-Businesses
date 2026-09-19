"""Database-Aware Query Service for Inventory Management.

Executes parameterized, read-only analytical queries against MongoDB,
strictly scoped to the authenticated user's shop_id.
Generates synchronized dual outputs: structured data for conversational UI cards
and identical natural-language spoken text in English, Hindi/Hinglish, or Telugu/Telugish.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from app.services.product_matcher import ProductMatcher


def _safe_oid(val):
    try:
        return ObjectId(str(val))
    except (InvalidId, TypeError, ValueError):
        return None


def _format_num(val) -> str:
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else str(round(f, 2))
    except Exception:
        return str(val)


def resolve_date_range(time_range: Optional[str], shop_tz_str: str = "Asia/Kolkata") -> Optional[Tuple[datetime, datetime]]:
    """Resolve human time range string into UTC [start, end] datetimes."""
    if not time_range:
        return None

    norm = time_range.lower().strip().replace("-", "_").replace(" ", "_")
    tz = None
    if ZoneInfo:
        try:
            tz = ZoneInfo(shop_tz_str)
        except Exception:
            pass
    if tz is None:
        tz = timezone(timedelta(hours=5, minutes=30))

    now_local = datetime.now(tz)

    if norm in ("today", "aaj", "eroju"):
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif norm in ("yesterday", "kal", "ninna"):
        y_local = now_local - timedelta(days=1)
        start_local = y_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = y_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif norm in ("this_week", "week", "is_hafte", "ee_vaaram"):
        start_local = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = now_local
    elif norm in ("this_month", "month", "is_mahine", "ee_nela"):
        start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_local = now_local
    elif norm in ("last_7_days", "7_days", "7days", "pichle_7_din"):
        start_local = now_local - timedelta(days=7)
        end_local = now_local
    elif norm in ("last_30_days", "30_days", "30days", "pichle_30_din"):
        start_local = now_local - timedelta(days=30)
        end_local = now_local
    else:
        return None

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


class QueryService:
    """Service executing read-only conversational database queries."""

    def __init__(self):
        self.matcher = ProductMatcher()

    async def get_shop_timezone(self, db: AsyncIOMotorDatabase, shop_id: str) -> str:
        """Fetch configured timezone for shop, defaulting to Asia/Kolkata."""
        shop = await db.shops.find_one({"_id": _safe_oid(shop_id)} or {"_id": shop_id})
        if not shop:
            shop = await db.shops.find_one({"_id": shop_id})
        return shop.get("timezone", "Asia/Kolkata") if shop else "Asia/Kolkata"

    async def execute_query(
        self,
        db: AsyncIOMotorDatabase,
        shop_id: str,
        intent: str,
        params: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Route and execute a database query based on intent, returning synchronized UI/voice response."""
        shop_tz = await self.get_shop_timezone(db, shop_id)
        time_range = params.get("time_range")
        date_bounds = resolve_date_range(time_range, shop_tz) if time_range else None

        # Route to query handler
        if intent in ("COUNT_PRODUCTS",):
            if time_range:
                return await self._query_count_products_added(db, shop_id, date_bounds, time_range, language)
            return await self._query_count_products(db, shop_id, language)

        elif intent in ("COUNT_PRODUCTS_ADDED",):
            tr = time_range or "today"
            bounds = date_bounds or resolve_date_range(tr, shop_tz)
            return await self._query_count_products_added(db, shop_id, bounds, tr, language)

        elif intent in ("LIST_PRODUCTS_ADDED",):
            tr = time_range or "today"
            bounds = date_bounds or resolve_date_range(tr, shop_tz)
            return await self._query_list_products_added(db, shop_id, bounds, tr, language)

        elif intent in ("COUNT_TRANSACTIONS", "COUNT_STOCK_IN", "COUNT_STOCK_OUT"):
            op = params.get("operation")
            if intent == "COUNT_STOCK_IN":
                op = "STOCK_IN"
            elif intent == "COUNT_STOCK_OUT":
                op = "STOCK_OUT"
            tr = time_range or "today"
            bounds = date_bounds or resolve_date_range(tr, shop_tz)
            return await self._query_count_transactions(db, shop_id, op, bounds, tr, language)

        elif intent in ("GET_TODAY_ACTIVITY", "GET_STOCK_MOVEMENT"):
            return await self._query_today_activity(db, shop_id, shop_tz, language)

        elif intent in ("LIST_LOW_STOCK", "LOW_STOCK_QUERY"):
            return await self._query_list_low_stock(db, shop_id, language)

        elif intent in ("LIST_OUT_OF_STOCK",):
            return await self._query_list_out_of_stock(db, shop_id, language)

        elif intent in ("GET_PRODUCT_STOCK", "STOCK_QUERY", "GET_CURRENT_STOCK"):
            product_text = params.get("product_text") or params.get("product") or ""
            return await self._query_product_stock(db, shop_id, product_text, language)

        elif intent in ("GET_TOP_STOCK_PRODUCTS",):
            order = params.get("order", "highest")
            return await self._query_top_stock(db, shop_id, order, language)

        elif intent in ("GET_RECENT_TRANSACTIONS",):
            limit = int(params.get("limit", 5))
            return await self._query_recent_transactions(db, shop_id, limit, language)

        else:
            return {
                "status": "error",
                "query_type": "UNKNOWN",
                "title": "Query Not Supported",
                "display_text": "I could not find an answer to that question in your inventory.",
                "message": "Samajh nahi aaya. Kripya doobara boliye." if language in ("hinglish", "hi", "hi_deva") else "I could not answer that question.",
                "structured_data": {},
            }

    # ------------------ Concrete Query Handlers ------------------

    async def _query_count_products(
        self, db: AsyncIOMotorDatabase, shop_id: str, language: str
    ) -> Dict[str, Any]:
        count = await db.products.count_documents({"shop_id": shop_id, "active": True})
        
        # Dual outputs
        if language in ("hinglish", "hi", "hi_deva"):
            spoken = f"Aapke paas kul {count} products hain."
            display = f"📦 Total {count} products hain."
        elif language in ("telugish", "te", "te_script"):
            spoken = f"Mee daggara motham {count} products unnai."
            display = f"📦 Motham {count} products unnai."
        else:
            spoken = f"You have {count} total products."
            display = f"📦 Total {count} products in inventory."

        return {
            "status": "answered",
            "query_type": "COUNT_PRODUCTS",
            "title": "Total Products",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": count,
                "entity": "products",
                "time_range": "all_time",
            },
        }

    async def _query_count_products_added(
        self,
        db: AsyncIOMotorDatabase,
        shop_id: str,
        date_bounds: Optional[Tuple[datetime, datetime]],
        time_range: str,
        language: str,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"shop_id": shop_id, "active": True}
        if date_bounds:
            query["created_at"] = {"$gte": date_bounds[0], "$lte": date_bounds[1]}

        count = await db.products.count_documents(query)
        period_label = time_range.replace("_", " ")

        if language in ("hinglish", "hi", "hi_deva"):
            if time_range == "today":
                spoken = f"Aaj {count} products add kiye gaye hain." if count > 0 else "Aaj koi product add nahi hua."
                display = f"📦 Aaj {count} products add huye."
            elif time_range == "this_week":
                spoken = f"Is hafte {count} products add kiye gaye hain." if count > 0 else "Is hafte koi product add nahi hua."
                display = f"📦 Is hafte {count} products add huye."
            else:
                spoken = f"{period_label} me {count} products add huye."
                display = f"📦 {period_label}: {count} products added."
        elif language in ("telugish", "te", "te_script"):
            if time_range == "today":
                spoken = f"Eroju {count} products add cheyabadindi." if count > 0 else "Eroju ae product add kaledu."
                display = f"📦 Eroju {count} products add ayyayi."
            elif time_range == "this_week":
                spoken = f"Ee vaaram {count} products add cheyabadindi." if count > 0 else "Ee vaaram ae product add kaledu."
                display = f"📦 Ee vaaram {count} products add ayyayi."
            else:
                spoken = f"{period_label} lo {count} products add ayyayi."
                display = f"📦 {period_label}: {count} products added."
        else:
            if count == 0:
                spoken = f"No products were added {period_label}."
                display = f"📦 No products were added {period_label}."
            elif count == 1:
                spoken = f"1 product was added {period_label}."
                display = f"📦 1 product was added {period_label}."
            else:
                spoken = f"{count} products were added {period_label}."
                display = f"📦 {count} products were added {period_label}."

        return {
            "status": "answered",
            "query_type": "COUNT_PRODUCTS_ADDED",
            "title": f"Products Added ({period_label.title()})",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": count,
                "time_range": time_range,
                "entity": "products_added",
            },
        }

    async def _query_list_products_added(
        self,
        db: AsyncIOMotorDatabase,
        shop_id: str,
        date_bounds: Optional[Tuple[datetime, datetime]],
        time_range: str,
        language: str,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"shop_id": shop_id, "active": True}
        if date_bounds:
            query["created_at"] = {"$gte": date_bounds[0], "$lte": date_bounds[1]}

        cursor = db.products.find(query).sort("created_at", -1).limit(20)
        docs = await cursor.to_list(length=20)
        items = [
            {
                "product_id": str(d["_id"]),
                "name": d.get("display_name", d.get("name", "")),
                "category": d.get("category", ""),
                "base_unit": d.get("base_unit", "piece"),
            }
            for d in docs
        ]
        names = [i["name"] for i in items]
        period_label = time_range.replace("_", " ")

        if not items:
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"Is samay ({period_label}) koi product add nahi hua."
                display = f"Koi product add nahi hua ({period_label})."
            elif language in ("telugish", "te", "te_script"):
                spoken = f"{period_label} lo ae product add kaledu."
                display = f"Ae product add kaledu ({period_label})."
            else:
                spoken = f"No products were added {period_label}."
                display = f"No products added {period_label}."
        else:
            names_str = ", ".join(names[:5])
            if len(names) > 5:
                names_str += f" and {len(names) - 5} more"
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"{period_label} me ye products add huye: {names_str}."
                display = f"Added {period_label}: {names_str}"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"{period_label} lo ee products add ayyayi: {names_str}."
                display = f"Added {period_label}: {names_str}"
            else:
                spoken = f"Products added {period_label}: {names_str}."
                display = f"Products added {period_label}: {names_str}"

        return {
            "status": "answered",
            "query_type": "LIST_PRODUCTS_ADDED",
            "title": f"Products Added ({period_label.title()})",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": len(items),
                "items": items,
                "time_range": time_range,
            },
        }

    async def _query_count_transactions(
        self,
        db: AsyncIOMotorDatabase,
        shop_id: str,
        operation: Optional[str],
        date_bounds: Optional[Tuple[datetime, datetime]],
        time_range: str,
        language: str,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"shop_id": shop_id}
        if operation:
            query["operation"] = operation.upper()

        if date_bounds:
            query["$or"] = [
                {"timestamp": {"$gte": date_bounds[0], "$lte": date_bounds[1]}},
                {"created_at": {"$gte": date_bounds[0], "$lte": date_bounds[1]}},
            ]

        count = await db.transactions.count_documents(query)
        period_label = time_range.replace("_", " ")

        op_name = "transactions"
        if operation == "STOCK_IN":
            op_name = "stock-in transactions"
        elif operation == "STOCK_OUT":
            op_name = "stock-out transactions"

        if language in ("hinglish", "hi", "hi_deva"):
            if operation == "STOCK_IN":
                spoken = f"Aaj {count} stock-in transactions huye hain." if time_range == "today" else f"{period_label} me {count} stock-in transactions huye."
                display = f"📥 {count} Stock-in transactions ({period_label})."
            elif operation == "STOCK_OUT":
                spoken = f"Aaj {count} stock-out transactions huye hain." if time_range == "today" else f"{period_label} me {count} stock-out transactions huye."
                display = f"📤 {count} Stock-out transactions ({period_label})."
            else:
                spoken = f"{period_label} me kul {count} transactions huye hain."
                display = f"📊 {count} Transactions ({period_label})."
        elif language in ("telugish", "te", "te_script"):
            if operation == "STOCK_IN":
                spoken = f"Eroju {count} stock-in transactions jarigayi." if time_range == "today" else f"{period_label} lo {count} stock-in transactions jarigayi."
                display = f"📥 {count} Stock-in transactions ({period_label})."
            elif operation == "STOCK_OUT":
                spoken = f"Eroju {count} stock-out transactions jarigayi." if time_range == "today" else f"{period_label} lo {count} stock-out transactions jarigayi."
                display = f"📤 {count} Stock-out transactions ({period_label})."
            else:
                spoken = f"{period_label} lo motham {count} transactions jarigayi."
                display = f"📊 {count} Transactions ({period_label})."
        else:
            spoken = f"{count} {op_name} happened {period_label}."
            display = f"{count} {op_name.title()} ({period_label.title()})."

        return {
            "status": "answered",
            "query_type": "COUNT_TRANSACTIONS",
            "title": f"{op_name.title()}",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": count,
                "operation": operation or "ALL",
                "time_range": time_range,
            },
        }

    async def _query_today_activity(
        self, db: AsyncIOMotorDatabase, shop_id: str, shop_tz: str, language: str
    ) -> Dict[str, Any]:
        bounds = resolve_date_range("today", shop_tz)
        time_cond = {"$or": [
            {"timestamp": {"$gte": bounds[0], "$lte": bounds[1]}},
            {"created_at": {"$gte": bounds[0], "$lte": bounds[1]}},
        ]} if bounds else {}

        in_count = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_IN", **time_cond})
        out_count = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_OUT", **time_cond})
        
        prod_cond = {"shop_id": shop_id, "active": True}
        if bounds:
            prod_cond["created_at"] = {"$gte": bounds[0], "$lte": bounds[1]}
        prod_count = await db.products.count_documents(prod_cond)

        if language in ("hinglish", "hi", "hi_deva"):
            spoken = f"Aaj ki activity: {in_count} stock-in, {out_count} stock-out, aur {prod_count} naye products add huye hain."
            display = f"📊 Aaj: {in_count} Stock In, {out_count} Stock Out, {prod_count} Products Added."
        elif language in ("telugish", "te", "te_script"):
            spoken = f"Eroju activity: {in_count} stock-in, {out_count} stock-out, mariyu {prod_count} kotha products add ayyayi."
            display = f"📊 Eroju: {in_count} Stock In, {out_count} Stock Out, {prod_count} Products Added."
        else:
            spoken = f"Today's activity: {in_count} stock-in, {out_count} stock-out, and {prod_count} products added."
            display = f"📊 Today: {in_count} In, {out_count} Out, {prod_count} Added."

        return {
            "status": "answered",
            "query_type": "GET_TODAY_ACTIVITY",
            "title": "Today's Inventory Activity",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "today_stock_in": in_count,
                "today_stock_out": out_count,
                "products_added": prod_count,
                "total_transactions": in_count + out_count,
                "time_range": "today",
            },
        }

    async def _query_list_low_stock(
        self, db: AsyncIOMotorDatabase, shop_id: str, language: str
    ) -> Dict[str, Any]:
        balances = await db.stock_balances.find({"shop_id": shop_id}).to_list(length=2000)
        products = await db.products.find({"shop_id": shop_id, "active": True}).to_list(length=2000)
        pmap = {str(p["_id"]): p for p in products}

        low_items = []
        for b in balances:
            pid = str(b.get("product_id", ""))
            p = pmap.get(pid)
            if not p:
                continue
            threshold = float(p.get("reorder_threshold", 0))
            qty = float(b.get("quantity", 0))
            if 0 < qty <= threshold:
                low_items.append({
                    "product_id": pid,
                    "product_name": p.get("display_name", p.get("name", "")),
                    "quantity": qty,
                    "unit": b.get("unit", p.get("base_unit", "piece")),
                    "threshold": threshold,
                })

        if not low_items:
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = "Sabhi items ka stock theek hai. Koi bhi item low stock nahi hai."
                display = "✅ Sabhi items stock me hain."
            elif language in ("telugish", "te", "te_script"):
                spoken = "Anni items baaga stock lo unnai. Thakkuva stock ae item ledu."
                display = "✅ Anni items stock lo unnai."
            else:
                spoken = "All items are well stocked. No items are running low."
                display = "✅ All items are well stocked."
        else:
            names_formatted = ", ".join([f"{i['product_name']} ({_format_num(i['quantity'])} {i['unit']})" for i in low_items[:4]])
            if len(low_items) > 4:
                names_formatted += f" aur {len(low_items) - 4} aur"
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"{len(low_items)} products ka stock kam hai: {names_formatted}."
                display = f"⚠️ {len(low_items)} Low Stock Products: {names_formatted}"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"{len(low_items)} products thakkuva stock lo unnai: {names_formatted}."
                display = f"⚠️ {len(low_items)} Low Stock Products: {names_formatted}"
            else:
                spoken = f"{len(low_items)} products are low in stock: {names_formatted}."
                display = f"⚠️ {len(low_items)} Low Stock: {names_formatted}"

        return {
            "status": "answered",
            "query_type": "LIST_LOW_STOCK",
            "title": "Low Stock Items",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": len(low_items),
                "items": low_items,
            },
        }

    async def _query_list_out_of_stock(
        self, db: AsyncIOMotorDatabase, shop_id: str, language: str
    ) -> Dict[str, Any]:
        balances = await db.stock_balances.find({"shop_id": shop_id}).to_list(length=2000)
        bmap = {str(b.get("product_id", "")): float(b.get("quantity", 0)) for b in balances}
        products = await db.products.find({"shop_id": shop_id, "active": True}).to_list(length=2000)

        out_items = []
        for p in products:
            pid = str(p["_id"])
            qty = bmap.get(pid, 0.0)
            if qty <= 0:
                out_items.append({
                    "product_id": pid,
                    "product_name": p.get("display_name", p.get("name", "")),
                    "quantity": 0.0,
                    "unit": p.get("base_unit", "piece"),
                })

        if not out_items:
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = "Koi bhi product out of stock nahi hai."
                display = "✅ Koi bhi product out of stock nahi hai."
            elif language in ("telugish", "te", "te_script"):
                spoken = "Ae product out of stock kaledu."
                display = "✅ Ae product out of stock kaledu."
            else:
                spoken = "No products are out of stock."
                display = "✅ No products are out of stock."
        else:
            names = ", ".join([i["product_name"] for i in out_items[:5]])
            if len(out_items) > 5:
                names += f" and {len(out_items) - 5} more"
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"{len(out_items)} products out of stock hain: {names}."
                display = f"🚫 Out of Stock: {names}"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"{len(out_items)} products out of stock lo unnai: {names}."
                display = f"🚫 Out of Stock: {names}"
            else:
                spoken = f"{len(out_items)} products are out of stock: {names}."
                display = f"🚫 Out of Stock: {names}"

        return {
            "status": "answered",
            "query_type": "LIST_OUT_OF_STOCK",
            "title": "Out of Stock Products",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": len(out_items),
                "items": out_items,
            },
        }

    async def _query_product_stock(
        self, db: AsyncIOMotorDatabase, shop_id: str, product_text: str, language: str
    ) -> Dict[str, Any]:
        if not product_text:
            return {
                "status": "error",
                "query_type": "GET_PRODUCT_STOCK",
                "title": "Product Required",
                "display_text": "Please specify which product stock you want to check.",
                "message": "Kripya batayein kaunse product ka stock check karna hai." if language in ("hinglish", "hi", "hi_deva") else "Which product do you want to check?",
                "structured_data": {},
            }

        match = await self.matcher.match_product(db, shop_id, product_text)
        if not match.product:
            candidates = [c.get("display_name", c.get("name", "")) for c in (match.candidates or [])]
            if candidates:
                cand_str = ", ".join(candidates[:3])
                msg = f"Multiple items match '{product_text}': {cand_str}."
            else:
                msg = f"Product '{product_text}' not found."
            return {
                "status": "error",
                "query_type": "GET_PRODUCT_STOCK",
                "title": "Product Not Found",
                "display_text": msg,
                "message": msg,
                "structured_data": {"candidates": candidates},
            }

        prod = match.product
        pid = str(prod["_id"])
        name = prod.get("display_name", prod.get("name", ""))
        balance_doc = await db.stock_balances.find_one({"shop_id": shop_id, "product_id": pid})
        qty = float(balance_doc["quantity"]) if balance_doc else 0.0
        unit = prod.get("base_unit", "piece")
        threshold = float(prod.get("reorder_threshold", 0))

        status_label = "IN_STOCK"
        if qty <= 0:
            status_label = "OUT_OF_STOCK"
        elif qty <= threshold:
            status_label = "LOW_STOCK"

        qty_str = _format_num(qty)
        if language in ("hinglish", "hi", "hi_deva"):
            spoken = f"{name} ka current stock {qty_str} {unit} hai."
            display = f"📦 {name}: {qty_str} {unit} available ({status_label})"
        elif language in ("telugish", "te", "te_script"):
            spoken = f"{name} prasthutham {qty_str} {unit} undi."
            display = f"📦 {name}: {qty_str} {unit} available ({status_label})"
        else:
            spoken = f"{qty_str} {unit} of {name} is currently available."
            display = f"📦 {name}: {qty_str} {unit} available ({status_label})"

        return {
            "status": "answered",
            "query_type": "GET_PRODUCT_STOCK",
            "title": f"Stock: {name}",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "product_id": pid,
                "product_name": name,
                "quantity": qty,
                "unit": unit,
                "threshold": threshold,
                "status": status_label,
            },
        }

    async def _query_top_stock(
        self, db: AsyncIOMotorDatabase, shop_id: str, order: str, language: str
    ) -> Dict[str, Any]:
        balances = await db.stock_balances.find({"shop_id": shop_id}).to_list(length=2000)
        products = await db.products.find({"shop_id": shop_id, "active": True}).to_list(length=2000)
        pmap = {str(p["_id"]): p for p in products}

        items = []
        for b in balances:
            pid = str(b.get("product_id", ""))
            p = pmap.get(pid)
            if not p:
                continue
            items.append({
                "product_id": pid,
                "product_name": p.get("display_name", p.get("name", "")),
                "quantity": float(b.get("quantity", 0)),
                "unit": b.get("unit", p.get("base_unit", "piece")),
            })

        is_highest = (order or "highest").lower() == "highest"
        items.sort(key=lambda x: x["quantity"], reverse=is_highest)
        top = items[:5]

        if not top:
            return {
                "status": "answered",
                "query_type": "GET_TOP_STOCK_PRODUCTS",
                "title": "Stock Ranking",
                "display_text": "No products in inventory yet.",
                "message": "Inventory me koi product nahi hai.",
                "structured_data": {"items": []},
            }

        first = top[0]
        f_qty = _format_num(first["quantity"])
        if is_highest:
            title = "Highest Stock Products"
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"Sabse jyada stock {first['product_name']} ka hai: {f_qty} {first['unit']}."
                display = f"🏆 Highest Stock: {first['product_name']} ({f_qty} {first['unit']})"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"Ekkuva stock unna product {first['product_name']}: {f_qty} {first['unit']}."
                display = f"🏆 Highest Stock: {first['product_name']} ({f_qty} {first['unit']})"
            else:
                spoken = f"The product with highest stock is {first['product_name']} with {f_qty} {first['unit']}."
                display = f"🏆 Highest Stock: {first['product_name']} ({f_qty} {first['unit']})"
        else:
            title = "Lowest Stock Products"
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"Sabse kam stock {first['product_name']} ka hai: {f_qty} {first['unit']}."
                display = f"⚠️ Lowest Stock: {first['product_name']} ({f_qty} {first['unit']})"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"Thakkuva stock unna product {first['product_name']}: {f_qty} {first['unit']}."
                display = f"⚠️ Lowest Stock: {first['product_name']} ({f_qty} {first['unit']})"
            else:
                spoken = f"The product with lowest stock is {first['product_name']} with {f_qty} {first['unit']}."
                display = f"⚠️ Lowest Stock: {first['product_name']} ({f_qty} {first['unit']})"

        return {
            "status": "answered",
            "query_type": "GET_TOP_STOCK_PRODUCTS",
            "title": title,
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "order": "highest" if is_highest else "lowest",
                "items": top,
            },
        }

    async def _query_recent_transactions(
        self, db: AsyncIOMotorDatabase, shop_id: str, limit: int, language: str
    ) -> Dict[str, Any]:
        cursor = db.transactions.find({"shop_id": shop_id}).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)

        products = await db.products.find({"shop_id": shop_id}).to_list(length=2000)
        pmap = {str(p["_id"]): p.get("display_name", p.get("name", "")) for p in products}

        txns = []
        for d in docs:
            pid = str(d.get("product_id", ""))
            ts = d.get("timestamp") or d.get("created_at") or datetime.now(timezone.utc)
            txns.append({
                "transaction_id": str(d.get("_id", "")),
                "product_name": pmap.get(pid, "Unknown Item"),
                "operation": d.get("operation", "STOCK_IN"),
                "quantity": float(d.get("quantity", 0)),
                "unit": d.get("unit", "piece"),
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            })

        if not txns:
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = "Koi recent transaction nahi mila."
                display = "Koi transaction record nahi hai."
            elif language in ("telugish", "te", "te_script"):
                spoken = "Ae recent transactions ledu."
                display = "Ae transactions record ledu."
            else:
                spoken = "No recent transactions found."
                display = "No recent transactions."
        else:
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"Ye rahi aakhiri {len(txns)} transactions."
                display = f"📝 Aakhiri {len(txns)} transactions."
            elif language in ("telugish", "te", "te_script"):
                spoken = f"Ivi chivari {len(txns)} transactions."
                display = f"📝 Chivari {len(txns)} transactions."
            else:
                spoken = f"Here are the latest {len(txns)} transactions."
                display = f"📝 Latest {len(txns)} transactions."

        return {
            "status": "answered",
            "query_type": "GET_RECENT_TRANSACTIONS",
            "title": "Recent Transactions",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": len(txns),
                "transactions": txns,
            },
        }
