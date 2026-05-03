from db import get_connection
from bson.objectid import ObjectId
from datetime import datetime
from services.category_service import get_categories_for_user

def add_transaction(user_id, household_id, category_id, amount, transaction_date, scope, transaction_desc=None):
    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    date_obj = datetime.strptime(transaction_date, '%Y-%m-%d')
    
    # Resolve category details for denormalization
    all_cats = get_categories_for_user(user_id, household_id)
    cat = next((c for c in all_cats if str(c["_id"]) == str(category_id)), None)
    
    transaction = {
        "transaction_id": ObjectId(),
        "user_id": ObjectId(user_id),
        "category_id": ObjectId(category_id),
        "category_name": cat["name"] if cat else "Unknown",
        "category_type": cat["type"] if cat else "expenses",
        "amount": float(amount),
        "date": date_obj,
        "description": transaction_desc
    }

    db.ledgers.update_one(
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "month": date_obj.month,
            "year": date_obj.year
        },
        {"$push": {"transactions": transaction}},
        upsert=True
    )


def get_user_categories(user_id, household_id=None, scope=None, category_type=None):
    db = get_connection()
    categories = []

    if scope in [None, 'individual']:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user and "categories" in user:
            for c in user["categories"]:
                if category_type and c.get("type") != category_type:
                    continue
                categories.append({
                    "category_id": str(c["_id"]),
                    "category_name": c["name"],
                    "category_type": c.get("type"),
                    "scope": "individual"
                })

    if scope in [None, 'household'] and household_id:
        household = db.households.find_one({"_id": ObjectId(household_id)})
        if household and "categories" in household:
            for c in household["categories"]:
                if category_type and c.get("type") != category_type:
                    continue
                categories.append({
                    "category_id": str(c["_id"]),
                    "category_name": c["name"],
                    "category_type": c.get("type"),
                    "scope": "household"
                })

    return sorted(categories, key=lambda x: x["category_name"])