import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase


def _get_demo_products(shop_id: str):
    """Return 10 demo products with multilingual aliases."""
    now = datetime.now(timezone.utc)
    return [
        {
            "shop_id": shop_id, "display_name": "Rice", "name": "Rice", "normalized_name": "rice",
            "aliases": [
                {"text": "rice", "normalized": "rice", "language": "en"},
                {"text": "chawal", "normalized": "chawal", "language": "hi"},
                {"text": "चावल", "normalized": "चावल", "language": "hi"},
                {"text": "biyyam", "normalized": "biyyam", "language": "te"},
                {"text": "బియ్యం", "normalized": "బియ్యం", "language": "te"},
            ],
            "category": "Grains", "base_unit": "kg",
            "allowed_units": ["kg", "bag", "g"],
            "conversions": [{"from_unit": "bag", "to_unit": "kg", "factor": 25}, {"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 50, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Sugar", "name": "Sugar", "normalized_name": "sugar",
            "aliases": [
                {"text": "sugar", "normalized": "sugar", "language": "en"},
                {"text": "chini", "normalized": "chini", "language": "hi"},
                {"text": "चीनी", "normalized": "चीनी", "language": "hi"},
                {"text": "chakkera", "normalized": "chakkera", "language": "te"},
                {"text": "చక్కెర", "normalized": "చక్కెర", "language": "te"},
            ],
            "category": "Groceries", "base_unit": "kg",
            "allowed_units": ["kg", "bag", "g"],
            "conversions": [{"from_unit": "bag", "to_unit": "kg", "factor": 50}, {"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 20, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Wheat Flour (Atta)", "name": "Wheat Flour", "normalized_name": "wheat flour",
            "aliases": [
                {"text": "atta", "normalized": "atta", "language": "hi"},
                {"text": "आटा", "normalized": "आटा", "language": "hi"},
                {"text": "godhuma pindi", "normalized": "godhuma pindi", "language": "te"},
            ],
            "category": "Grains", "base_unit": "kg",
            "allowed_units": ["kg", "bag", "g"],
            "conversions": [{"from_unit": "bag", "to_unit": "kg", "factor": 10}],
            "reorder_threshold": 30, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Cooking Oil", "name": "Cooking Oil", "normalized_name": "cooking oil",
            "aliases": [
                {"text": "oil", "normalized": "oil", "language": "en"},
                {"text": "tel", "normalized": "tel", "language": "hi"},
                {"text": "तेल", "normalized": "तेल", "language": "hi"},
                {"text": "nune", "normalized": "nune", "language": "te"},
                {"text": "నూనె", "normalized": "నూనె", "language": "te"},
            ],
            "category": "Oils", "base_unit": "litre",
            "allowed_units": ["litre", "ml", "bottle"],
            "conversions": [{"from_unit": "ml", "to_unit": "litre", "factor": 0.001}],
            "reorder_threshold": 15, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Soap (Surf)", "name": "Soap", "normalized_name": "soap",
            "aliases": [
                {"text": "surf", "normalized": "surf", "language": "en"},
                {"text": "sabun", "normalized": "sabun", "language": "hi"},
                {"text": "साबुन", "normalized": "साबुन", "language": "hi"},
                {"text": "sabbu", "normalized": "sabbu", "language": "te"},
            ],
            "category": "Household", "base_unit": "carton",
            "allowed_units": ["carton", "piece", "box"],
            "conversions": [{"from_unit": "box", "to_unit": "carton", "factor": 1}],
            "reorder_threshold": 10, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Dal (Toor)", "name": "Dal", "normalized_name": "dal",
            "aliases": [
                {"text": "daal", "normalized": "daal", "language": "hi"},
                {"text": "दाल", "normalized": "दाल", "language": "hi"},
                {"text": "pappu", "normalized": "pappu", "language": "te"},
                {"text": "పప్పు", "normalized": "పప్పు", "language": "te"},
            ],
            "category": "Lentils", "base_unit": "kg",
            "allowed_units": ["kg", "g", "bag"],
            "conversions": [{"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 25, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Salt", "name": "Salt", "normalized_name": "salt",
            "aliases": [
                {"text": "namak", "normalized": "namak", "language": "hi"},
                {"text": "नमक", "normalized": "नमक", "language": "hi"},
                {"text": "uppu", "normalized": "uppu", "language": "te"},
                {"text": "ఉప్పు", "normalized": "ఉప్పు", "language": "te"},
            ],
            "category": "Groceries", "base_unit": "kg",
            "allowed_units": ["kg", "g", "packet"],
            "conversions": [{"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 10, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Tea (Chai)", "name": "Tea", "normalized_name": "tea",
            "aliases": [
                {"text": "chai", "normalized": "chai", "language": "hi"},
                {"text": "चाय", "normalized": "चाय", "language": "hi"},
                {"text": "tea podi", "normalized": "tea podi", "language": "te"},
            ],
            "category": "Beverages", "base_unit": "kg",
            "allowed_units": ["kg", "g", "packet"],
            "conversions": [{"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 5, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Milk", "name": "Milk", "normalized_name": "milk",
            "aliases": [
                {"text": "doodh", "normalized": "doodh", "language": "hi"},
                {"text": "दूध", "normalized": "दूध", "language": "hi"},
                {"text": "palu", "normalized": "palu", "language": "te"},
                {"text": "పాలు", "normalized": "పాలు", "language": "te"},
            ],
            "category": "Dairy", "base_unit": "litre",
            "allowed_units": ["litre", "ml", "packet"],
            "conversions": [{"from_unit": "ml", "to_unit": "litre", "factor": 0.001}],
            "reorder_threshold": 20, "active": True, "created_at": now, "updated_at": now,
        },
        {
            "shop_id": shop_id, "display_name": "Onion", "name": "Onion", "normalized_name": "onion",
            "aliases": [
                {"text": "pyaz", "normalized": "pyaz", "language": "hi"},
                {"text": "प्याज", "normalized": "प्याज", "language": "hi"},
                {"text": "ullipaya", "normalized": "ullipaya", "language": "te"},
                {"text": "ఉల్లిపాయ", "normalized": "ఉల్లిపాయ", "language": "te"},
            ],
            "category": "Vegetables", "base_unit": "kg",
            "allowed_units": ["kg", "g", "bag"],
            "conversions": [{"from_unit": "g", "to_unit": "kg", "factor": 0.001}],
            "reorder_threshold": 30, "active": True, "created_at": now, "updated_at": now,
        },
    ]


async def seed_demo_data(db: AsyncIOMotorDatabase, shop_id: str):
    """Seed demo products and initial stock balances for a shop (idempotent)."""
    existing = await db.products.count_documents({"shop_id": shop_id})
    if existing > 0:
        return
    now = datetime.now(timezone.utc)
    products = _get_demo_products(shop_id)

    # Insert products
    result = await db.products.insert_many(products)
    inserted_ids = result.inserted_ids

    # Create initial stock balances (realistic quantities)
    initial_quantities = [100, 40, 50, 20, 30, 35, 15, 3, 25, 45]
    balances = []
    for i, product_id in enumerate(inserted_ids):
        qty = initial_quantities[i] if i < len(initial_quantities) else 50
        balances.append({
            "shop_id": shop_id,
            "product_id": str(product_id),
            "quantity": float(qty),
            "unit": products[i]["base_unit"],
            "updated_at": now,
            "version": 1,
        })

    await db.stock_balances.insert_many(balances)

    # Create some low-stock alerts for products below threshold
    for i, product_id in enumerate(inserted_ids):
        qty = initial_quantities[i] if i < len(initial_quantities) else 50
        threshold = products[i]["reorder_threshold"]
        if qty <= threshold:
            await db.alerts.insert_one({
                "shop_id": shop_id,
                "product_id": str(product_id),
                "alert_type": "LOW_STOCK",
                "type": "LOW_STOCK",
                "status": "OPEN",
                "current_quantity": qty,
                "threshold": threshold,
                "created_at": now,
            })


async def seed_data():
    """Standalone seed for running directly."""
    from app.db.mongodb import mongo_db
    from app.config import settings

    await mongo_db.connect(settings.MONGODB_URI, settings.DB_NAME)
    db = mongo_db.get_database()

    existing = await db.shops.find_one({"name": "Kumar General Store"})
    if existing:
        print("Data already seeded.")
        await mongo_db.disconnect()
        return

    shop_result = await db.shops.insert_one({
        "name": "Kumar General Store",
        "default_language": "en",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "created_at": datetime.now(timezone.utc),
    })
    shop_id = str(shop_result.inserted_id)

    await db.users.insert_one({
        "shop_id": shop_id,
        "name": "Demo Owner",
        "phone": "+919999999999",
        "role": "owner",
        "active": True,
        "created_at": datetime.now(timezone.utc),
    })

    await seed_demo_data(db, shop_id)
    print(f"Seeding complete for shop {shop_id}.")
    await mongo_db.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_data())
