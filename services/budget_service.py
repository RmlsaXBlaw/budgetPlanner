from db import get_connection
from bson.objectid import ObjectId
from services.category_service import get_categories_for_user

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

    # Resolve category details for denormalization
    all_cats = get_categories_for_user(user_id, household_id)
    cat = next((c for c in all_cats if str(c["_id"]) == str(category_id)), None)

    budget_entry = {
        "category_id": ObjectId(category_id),
        "category_name": cat["name"] if cat else "Unknown",
        "category_type": cat["type"] if cat else "expenses",
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
        {"$sort": {"year": -1, "month": -1}}
    ]
    
    return [
        {
            "budget_month": f"{doc['year']}-{doc['month']:02d}",
            "amount": float(doc["budgets"]["amount"]),
            "category": doc["budgets"].get("category_name", "Unknown"),
            "category_type": doc["budgets"].get("category_type", "Unknown"),
            "scope": "household" if doc["owner_type"] == "household" else "individual"
        }
        for doc in db.ledgers.aggregate(pipeline)
    ]
