from db import get_connection
from bson.objectid import ObjectId
from datetime import datetime

def add_transaction(user_id, household_id, category_id, amount, transaction_date, scope, transaction_desc=None):
    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    date_obj = datetime.strptime(transaction_date, '%Y-%m-%d')
    
    transaction = {
        "transaction_id": ObjectId(),
        "user_id": ObjectId(user_id),
        "category_id": ObjectId(category_id),
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
    query = {}

    if scope == 'individual':
        query["owner_type"] = "user"
        query["owner_id"] = ObjectId(user_id)
    elif scope == 'household':
        if household_id is None:
            return []
        query["owner_type"] = "household"
        query["owner_id"] = ObjectId(household_id)
    else:
        or_conditions = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
        if household_id:
            or_conditions.append({"owner_type": "household", "owner_id": ObjectId(household_id)})
        query["$or"] = or_conditions

    if category_type:
        query["type"] = category_type

    return [
        {
            "category_id": str(c["_id"]),
            "category_name": c["name"],
            "category_type": c["type"],
            "scope": "individual" if c["owner_type"] == "user" else "household"
        }
        for c in db.categories.find(query).sort("name", 1)
    ]