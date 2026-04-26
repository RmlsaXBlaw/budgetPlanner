from db import get_connection
from bson.objectid import ObjectId

def add_budget(user_id, household_id, category_id, amount, budget_month, budget_year, scope):
    """
    Dodaje nowy budzet
    
    scope:
    - 'individual' -> budzet przypisany do użytkownika
    - 'household' -> budzet przypisany do gospodarstwa domowego
    """
    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    budget_entry = {
        "category_id": ObjectId(category_id),
        "amount": float(amount)
    }
    
    query = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "month": int(budget_month),
        "year": int(budget_year)
    }

    # Remove existing budget for this category to replace it, preventing duplicates
    db.ledgers.update_one(query, {"$pull": {"budgets": {"category_id": ObjectId(category_id)}}}, upsert=False)
    
    # Add the budget into the specific ledger Document
    db.ledgers.update_one(query, {"$push": {"budgets": budget_entry}}, upsert=True)

def filter_budgets(user_id, household_id=None):
    db = get_connection()
    
    owner_query = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
    if household_id:
        owner_query.append({"owner_type": "household", "owner_id": ObjectId(household_id)})
        
    pipeline = [
        {"$match": {"$or": owner_query}},
        {"$unwind": "$budgets"},
        {
            "$lookup": {
                "from": "categories",
                "localField": "budgets.category_id",
                "foreignField": "_id",
                "as": "category_info"
            }
        },
        {"$unwind": "$category_info"},
        {"$sort": {"year": -1, "month": -1}}
    ]
    
    return [
        {
            "budget_month": f"{doc['year']}-{doc['month']:02d}",
            "amount": float(doc["budgets"]["amount"]),
            "category": doc["category_info"]["name"],
            "category_type": doc["category_info"]["type"],
            "scope": "household" if doc["owner_type"] == "household" else "individual"
        }
        for doc in db.ledgers.aggregate(pipeline)
    ]
