from datetime import datetime
from bson.objectid import ObjectId
from db import get_connection

def get_executive_summary(user_id, household_id=None, month=None, year=None, scope='individual'):
    """
    Returns total budget, total spent, and remaining amount, filtered by scope, month, and year.
    """
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    if scope == 'household' and not household_id:
        return {"total_budget": 0.0, "total_spent": 0.0, "total_remaining": 0.0}

    ledger = db.ledgers.find_one({
        "owner_type": owner_type,
        "owner_id": owner_id,
        "month": int(month),
        "year": int(year)
    }) or {}

    total_budget = sum(b.get("amount", 0) for b in ledger.get("budgets", []))

    category_query = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
    if household_id:
        category_query.append({"owner_type": "household", "owner_id": ObjectId(household_id)})

    expense_categories = {
        c["_id"] for c in db.categories.find({"$or": category_query, "type": "expenses"})
    }

    total_spent = sum(
        t.get("amount", 0) for t in ledger.get("transactions", [])
        if t.get("category_id") in expense_categories
    )

    return {
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent
    }


def get_detailed_budgets(user_id, household_id=None, month=None, year=None, scope='individual'):
    """
    Zwraca szczegółowe budget/spent per nazwa kategorii.
    Salary(income) i Salary(expenses) są traktowane jako jedna kategoria: Salary.
    """
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    if scope == 'household' and not household_id:
        return []

    category_query = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
    if household_id:
        category_query.append({"owner_type": "household", "owner_id": ObjectId(household_id)})

    categories = {c["_id"]: c["name"] for c in db.categories.find({"$or": category_query})}
    
    ledger = db.ledgers.find_one({
        "owner_type": owner_type,
        "owner_id": owner_id,
        "month": int(month),
        "year": int(year)
    }) or {"budgets": [], "transactions": []}

    budget_map = {}
    for b in ledger.get("budgets", []):
        budget_map[b["category_id"]] = budget_map.get(b["category_id"], 0) + b["amount"]

    spent_map = {}
    for t in ledger.get("transactions", []):
        spent_map[t["category_id"]] = spent_map.get(t["category_id"], 0) + t["amount"]

    result = []
    for cat_id, cat_name in categories.items():
        amount = float(budget_map.get(cat_id, 0))
        spent = float(spent_map.get(cat_id, 0))
        if amount > 0 or spent > 0:
            result.append({
                "category_name": cat_name,
                "scope": scope.upper(),
                "amount": amount,
                "spent": spent,
                "remaining": amount - spent
            })

    return sorted(result, key=lambda x: x["category_name"])

def get_transactions(user_id, household_id=None, start_date=None, end_date=None):
    db = get_connection()
    
    owner_query = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
    if household_id:
        owner_query.append({"owner_type": "household", "owner_id": ObjectId(household_id)})
        
    match_stage = {}
    if start_date and end_date:
        match_stage["transactions.date"] = {
            "$gte": datetime.strptime(start_date, '%Y-%m-%d'),
            "$lte": datetime.strptime(end_date, '%Y-%m-%d')
        }

    # MongoDB Aggregation Pipeline accurately recreates the flat cross-month relational search
    pipeline = [
        {"$match": {"$or": owner_query}},
        {"$unwind": "$transactions"},
    ]
    
    if match_stage:
        pipeline.append({"$match": match_stage})
        
    pipeline.extend([
        {"$sort": {"transactions.date": -1}}
    ])

    return [
        {
            "transaction_id": str(doc["transactions"]["transaction_id"]),
            "transaction_date": doc["transactions"]["date"].strftime('%Y-%m-%d'),
            "amount": float(doc["transactions"]["amount"]),
            "description": doc["transactions"].get("description", ""),
            "category": doc["transactions"].get("category_name", "Unknown"),
            "category_type": doc["transactions"].get("category_type", "Unknown"),
            "scope": "household" if doc["owner_type"] == "household" else "individual"
        }
        for doc in db.ledgers.aggregate(pipeline)
    ]


def get_expenditure_analysis(user_id, household_id, month, year, scope='individual'):
    db = get_connection()
    owner_type = 'user' if scope == 'individual' else 'household'
    owner_id = ObjectId(user_id) if scope == 'individual' else ObjectId(household_id)

    if scope == 'household' and not household_id:
        return []

    ledger = db.ledgers.find_one({
        "owner_type": owner_type,
        "owner_id": owner_id,
        "month": int(month),
        "year": int(year)
    }) or {}

    category_query = [{"owner_type": "user", "owner_id": ObjectId(user_id)}]
    if household_id:
        category_query.append({"owner_type": "household", "owner_id": ObjectId(household_id)})

    expense_cats = {
        c["_id"]: c["name"]
        for c in db.categories.find({"$or": category_query, "type": "expenses"})
    }

    analysis = {}
    for t in ledger.get("transactions", []):
        cid = t.get("category_id")
        if cid in expense_cats:
            cname = expense_cats[cid]
            analysis[cname] = analysis.get(cname, 0) + float(t["amount"])

    result = [{"category_name": k, "spent": v} for k, v in analysis.items()]
    result.sort(key=lambda x: x["spent"], reverse=True)
    return result