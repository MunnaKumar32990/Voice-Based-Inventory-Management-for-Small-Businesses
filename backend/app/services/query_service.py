"""Database-Aware Query Service for Inventory Management.

Executes parameterized, read-only analytical queries against MongoDB,
strictly scoped to the authenticated user's shop_id.
Generates synchronized dual outputs: structured data for conversational UI cards
and identical natural-language spoken text in English, Hindi/Hinglish, or Telugu/Telugish.
"""
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from app.config import settings
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
            transcript = params.get("transcript") or params.get("product_text") or intent
            return await self.ask_database_assistant(db, shop_id, transcript, language)

    async def ask_database_assistant(
        self,
        db: AsyncIOMotorDatabase,
        shop_id: str,
        transcript: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Conversational database assistant that answers ANY store question
        using a comprehensive live MongoDB snapshot including per-product
        transaction summaries, recent transaction log, and inventory state.
        """
        clean_text = transcript.strip() if transcript else ""
        shop = await db.shops.find_one({"_id": _safe_oid(shop_id)})
        if not shop:
            shop = await db.shops.find_one({"_id": shop_id})
        shop_name = shop.get("name", "Your Store") if shop else "Your Store"
        shop_tz = shop.get("timezone", "Asia/Kolkata") if shop else "Asia/Kolkata"

        # 1. Fetch live products and balances
        products = await db.products.find({"shop_id": shop_id, "active": True}).to_list(length=200)
        balances = await db.stock_balances.find({"shop_id": shop_id}).to_list(length=200)
        bmap = {str(b.get("product_id")): b for b in balances}
        pmap = {str(p["_id"]): p for p in products}
        name_map = {str(p["_id"]): p.get("display_name", p.get("name", "")) for p in products}

        catalog = []
        low_stock_items = []
        out_of_stock_items = []
        for p in products:
            pid = str(p["_id"])
            b = bmap.get(pid, {})
            qty = float(b.get("quantity", 0))
            unit = b.get("unit", p.get("base_unit", "piece"))
            thr = float(p.get("reorder_threshold", 0))
            status = "OK"
            if qty <= 0:
                status = "OUT_OF_STOCK"
                out_of_stock_items.append(p.get("display_name", p.get("name")))
            elif qty <= thr:
                status = "LOW_STOCK"
                low_stock_items.append(f"{p.get('display_name', p.get('name'))} ({_format_num(qty)} {unit})")
            catalog.append({
                "name": p.get("display_name", p.get("name")),
                "category": p.get("category", "General"),
                "stock": _format_num(qty),
                "unit": unit,
                "reorder_threshold": _format_num(thr),
                "status": status,
            })

        # 2. Fetch TODAY's activity counts
        today_bounds = resolve_date_range("today", shop_tz)
        today_cond = {"$or": [
            {"timestamp": {"$gte": today_bounds[0], "$lte": today_bounds[1]}},
            {"created_at": {"$gte": today_bounds[0], "$lte": today_bounds[1]}},
        ]} if today_bounds else {}

        today_in = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_IN", **today_cond})
        today_out = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_OUT", **today_cond})
        today_prod_added = await db.products.count_documents(
            {"shop_id": shop_id, "active": True, "created_at": {"$gte": today_bounds[0], "$lte": today_bounds[1]}}
        ) if today_bounds else 0

        # 3. Fetch THIS WEEK's activity counts
        week_bounds = resolve_date_range("this_week", shop_tz)
        week_cond = {"$or": [
            {"timestamp": {"$gte": week_bounds[0], "$lte": week_bounds[1]}},
            {"created_at": {"$gte": week_bounds[0], "$lte": week_bounds[1]}},
        ]} if week_bounds else {}
        week_in = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_IN", **week_cond})
        week_out = await db.transactions.count_documents({"shop_id": shop_id, "operation": "STOCK_OUT", **week_cond})

        # 4. Fetch per-product transaction summaries (ALL TIME + TODAY)
        all_txns = await db.transactions.find({"shop_id": shop_id}).to_list(length=5000)
        per_product = {}
        for tx in all_txns:
            pid = str(tx.get("product_id", ""))
            pname = name_map.get(pid, tx.get("product_name", pid))
            if pname not in per_product:
                per_product[pname] = {"total_in": 0, "total_out": 0, "total_in_qty": 0.0, "total_out_qty": 0.0,
                                       "today_in": 0, "today_out": 0, "today_in_qty": 0.0, "today_out_qty": 0.0,
                                       "unit": tx.get("unit", ""), "last_txn": None}
            entry = per_product[pname]
            op = tx.get("operation", "")
            qty = float(tx.get("quantity", 0))
            ts = tx.get("timestamp") or tx.get("created_at")
            if op == "STOCK_IN":
                entry["total_in"] += 1
                entry["total_in_qty"] += qty
            elif op == "STOCK_OUT":
                entry["total_out"] += 1
                entry["total_out_qty"] += qty
            if ts:
                if getattr(ts, "tzinfo", None) is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if entry["unit"] == "":
                    entry["unit"] = tx.get("unit", "")
                if entry["last_txn"] is None or ts > entry["last_txn"]:
                    entry["last_txn"] = ts
                # Check if today
                if today_bounds and today_bounds[0] <= ts <= today_bounds[1]:
                    if op == "STOCK_IN":
                        entry["today_in"] += 1
                        entry["today_in_qty"] += qty
                    elif op == "STOCK_OUT":
                        entry["today_out"] += 1
                        entry["today_out_qty"] += qty

        product_tx_summary = []
        for pname, e in per_product.items():
            product_tx_summary.append({
                "product": pname,
                "unit": e["unit"],
                "all_time_stock_in": f"{e['total_in']} transactions ({_format_num(e['total_in_qty'])} {e['unit']})",
                "all_time_stock_out": f"{e['total_out']} transactions ({_format_num(e['total_out_qty'])} {e['unit']})",
                "today_stock_in": f"{e['today_in']} transactions ({_format_num(e['today_in_qty'])} {e['unit']})",
                "today_stock_out": f"{e['today_out']} transactions ({_format_num(e['today_out_qty'])} {e['unit']})",
            })

        # 5. Fetch recent transactions (last 20) with product names
        recent_txns_raw = await db.transactions.find(
            {"shop_id": shop_id}
        ).sort("timestamp", -1).limit(20).to_list(length=20)
        recent_txns = []
        for tx in recent_txns_raw:
            pid = str(tx.get("product_id", ""))
            pname = name_map.get(pid, tx.get("product_name", pid))
            ts = tx.get("timestamp") or tx.get("created_at")
            recent_txns.append({
                "product": pname,
                "operation": tx.get("operation", ""),
                "quantity": _format_num(tx.get("quantity", 0)),
                "unit": tx.get("unit", ""),
                "time": ts.isoformat() if ts else "unknown",
            })

        # 6. Categories
        categories_list = sorted(list({p.get("category", "") for p in products if p.get("category")}))

        # 7. Call Gemini with comprehensive snapshot
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        if api_key:
            prompt = (
                f"You are the intelligent database-aware voice assistant for '{shop_name}'.\n"
                f"Answer the user's question ACCURATELY based ONLY on the live database snapshot below.\n"
                f"The user may speak in English, Hindi, Hinglish, Telugu, or mix languages.\n"
                f"ALWAYS respond in the SAME language/dialect the user speaks.\n\n"
                f"--- LIVE DATABASE SNAPSHOT ---\n"
                f"Total Active Products: {len(products)}\n"
                f"Product Categories ({len(categories_list)}): {json.dumps(categories_list)}\n"
                f"Products Catalog (name, category, current_stock, unit, reorder_threshold, status):\n{json.dumps(catalog[:40], indent=1)}\n\n"
                f"--- TODAY'S ACTIVITY ---\n"
                f"Today Stock-In Transactions: {today_in}\n"
                f"Today Stock-Out Transactions: {today_out}\n"
                f"Products Added Today: {today_prod_added}\n\n"
                f"--- THIS WEEK'S ACTIVITY ---\n"
                f"This Week Stock-In Transactions: {week_in}\n"
                f"This Week Stock-Out Transactions: {week_out}\n\n"
                f"--- PER-PRODUCT TRANSACTION SUMMARY ---\n"
                f"{json.dumps(product_tx_summary[:40], indent=1)}\n\n"
                f"--- RECENT TRANSACTIONS (latest 20) ---\n"
                f"{json.dumps(recent_txns[:20], indent=1)}\n\n"
                f"--- ALERTS ---\n"
                f"Low Stock Items ({len(low_stock_items)}): {', '.join(low_stock_items) if low_stock_items else 'None'}\n"
                f"Out of Stock Items ({len(out_of_stock_items)}): {', '.join(out_of_stock_items) if out_of_stock_items else 'None'}\n\n"
                f"--- USER QUESTION ---\n"
                f"Original transcript: \"{clean_text}\"\n"
                f"Detected Language/Dialect: {language}\n\n"
                f"--- INSTRUCTIONS ---\n"
                f"- Answer ANY question the user asks about the store's inventory, products, transactions, stock, categories, etc.\n"
                f"- For product-specific queries like 'total rice added' or 'rice ki kitni transaction hui', use the PER-PRODUCT TRANSACTION SUMMARY.\n"
                f"- For complex queries like 'total product entered today', count products added today ({today_prod_added}).\n"
                f"- For 'which is lowest stock' / 'sabse kam stock kiska hai', look at current stock levels in the catalog.\n"
                f"- If user asks in Hindi/Hinglish, reply in Hindi/Hinglish. If Telugu, reply in Telugu. If English, reply in English.\n"
                f"- Never say 'product not found' or 'I don't know' if the data is in the snapshot.\n"
                f"- Never invent data. Only use what's in the snapshot.\n"
                f"- Output strictly valid JSON:\n"
                f"{{\n"
                f'  "title": "Short descriptive title for UI card (max 6 words)",\n'
                f'  "query_type": "COUNT_PRODUCTS" | "COUNT_PRODUCTS_ADDED" | "COUNT_TRANSACTIONS" | "LIST_PRODUCTS" | "GET_PRODUCT_STOCK" | "GET_TODAY_ACTIVITY" | "GET_TOP_STOCK_PRODUCTS" | "CATEGORY_QUERY" | "GENERAL_QUERY",\n'
                f'  "display_text": "Visual summary text WITH emoji for UI card",\n'
                f'  "spoken_text": "Natural conversational spoken sentence for TTS in same language as user",\n'
                f'  "structured_data": {{\n'
                f'    "count": number or null,\n'
                f'    "items": [{{"product_name": "...", "quantity": number, "unit": "..."}}] or null,\n'
                f'    "entity": string or null,\n'
                f'    "today_stock_in": number or null,\n'
                f'    "today_stock_out": number or null,\n'
                f'    "products_added": number or null\n'
                f'  }}\n'
                f"}}\n"
            )

            models = [(settings.GEMINI_MODEL or "gemini-3-flash-preview").strip()]
            for model in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                    body = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.1,
                        }
                    }
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        resp = await client.post(
                            url,
                            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
                            json=body,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates") or []
                            if candidates:
                                text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                if text_out:
                                    parsed_resp = json.loads(text_out)
                                    return {
                                        "status": "answered",
                                        "query_type": parsed_resp.get("query_type", "GENERAL_QUERY"),
                                        "title": parsed_resp.get("title", "Store Information"),
                                        "display_text": parsed_resp.get("display_text", ""),
                                        "message": parsed_resp.get("spoken_text", parsed_resp.get("display_text", "")),
                                        "structured_data": parsed_resp.get("structured_data", {}),
                                    }
                except Exception:
                    continue

        # 8. Deterministic fallback if Gemini is offline
        clean_lower = clean_text.lower()
        if any(w in clean_lower for w in ("category", "categories", "kis type", "types", "vibhag")):
            cat_str = ", ".join(categories_list)
            if language in ("hinglish", "hi", "hi_deva"):
                spoken = f"Dukan me {len(categories_list)} categories hain: {cat_str}."
                display = f"📦 {len(categories_list)} Categories: {cat_str}"
            elif language in ("telugish", "te", "te_script"):
                spoken = f"Shop lo {len(categories_list)} categories unnai: {cat_str}."
                display = f"📦 {len(categories_list)} Categories: {cat_str}"
            else:
                spoken = f"There are {len(categories_list)} categories: {cat_str}."
                display = f"📦 {len(categories_list)} Categories: {cat_str}"
            return {
                "status": "answered",
                "query_type": "CATEGORY_QUERY",
                "title": "Store Categories",
                "display_text": display,
                "message": spoken,
                "structured_data": {"count": len(categories_list), "items": categories_list},
            }
        if any(w in clean_lower for w in ("lowest", "minimum", "least", "sabse kam", "thakkuva")):
            return await self._query_top_stock(db, shop_id, "lowest", language)
        if any(w in clean_lower for w in ("highest", "maximum", "most", "sabse jyada", "ekkuva")):
            return await self._query_top_stock(db, shop_id, "highest", language)
        if any(w in clean_lower for w in ("total", "product", "kitna", "kitne", "count", "kul", "motham")):
            return await self._query_count_products(db, shop_id, language)
        if any(w in clean_lower for w in ("activity", "aaj", "today", "hua", "movement")):
            return await self._query_today_activity(db, shop_id, shop_tz, language)
        if any(w in clean_lower for w in ("low", "kam", "shortage", "reorder")):
            return await self._query_list_low_stock(db, shop_id, language)
        if any(w in clean_lower for w in ("out of stock", "khatam")):
            return await self._query_list_out_of_stock(db, shop_id, language)

        # General store summary fallback
        if language in ("hinglish", "hi", "hi_deva"):
            spoken = f"Aapki dukan me kul {len(products)} products hain. Aaj {today_in} stock-in aur {today_out} stock-out transactions huye."
            display = f"📦 {len(products)} Products | Aaj: {today_in} In, {today_out} Out"
        else:
            spoken = f"You have {len(products)} products in your inventory. Today you had {today_in} stock-in and {today_out} stock-out transactions."
            display = f"📦 {len(products)} Products | Today: {today_in} In, {today_out} Out"

        return {
            "status": "answered",
            "query_type": "GET_TODAY_ACTIVITY",
            "title": "Inventory Overview",
            "display_text": display,
            "message": spoken,
            "structured_data": {
                "count": len(products),
                "today_stock_in": today_in,
                "today_stock_out": today_out,
                "products_added": today_prod_added,
            },
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
                return {
                    "status": "error",
                    "query_type": "GET_PRODUCT_STOCK",
                    "title": "Product Not Found",
                    "display_text": msg,
                    "message": msg,
                    "structured_data": {"candidates": candidates},
                }
            # Fallback to general conversational database assistant
            return await self.ask_database_assistant(db, shop_id, product_text, language)

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
