from db import get_connection

def backfill_embedded_categories():
    """
    One-off script to migrate old relational data to the new NoSQL embedded pattern.
    """
    db = get_connection()
    
    # Cache categories locally to avoid hitting the database for every single transaction
    print("Fetching categories...")
    categories = {c["_id"]: c for c in db.categories.find()}
    
    print("Processing ledgers...")
    ledgers = db.ledgers.find()
    updated_count = 0
    
    for ledger in ledgers:
        needs_update = False
        
        # Backfill budgets
        for budget in ledger.get("budgets", []):
            if "category_name" not in budget:
                cat = categories.get(budget.get("category_id"))
                budget["category_name"] = cat["name"] if cat else "Unknown"
                budget["category_type"] = cat["type"] if cat else "expenses"
                needs_update = True
        
        # Backfill transactions
        for tx in ledger.get("transactions", []):
            if "category_name" not in tx:
                cat = categories.get(tx.get("category_id"))
                tx["category_name"] = cat["name"] if cat else "Unknown"
                tx["category_type"] = cat["type"] if cat else "expenses"
                needs_update = True
                
        # Save back to database if modifications were made
        if needs_update:
            db.ledgers.update_one(
                {"_id": ledger["_id"]},
                {"$set": {
                    "budgets": ledger.get("budgets", []),
                    "transactions": ledger.get("transactions", [])
                }}
            )
            updated_count += 1
            
    print(f"Migration complete! Updated {updated_count} ledger documents.")

if __name__ == "__main__":
    backfill_embedded_categories()
