from db import get_connection

def migrate_categories():
    db = get_connection()
    print("Fetching categories for migration...")
    categories = list(db.categories.find())
    
    user_updates = 0
    household_updates = 0
    
    for cat in categories:
        embedded_cat = {
            "_id": cat["_id"],
            "name": cat["name"],
            "type": cat["type"]
        }
        
        if cat["owner_type"] == "user":
            result = db.users.update_one(
                {"_id": cat["owner_id"]},
                {"$addToSet": {"categories": embedded_cat}}
            )
            if result.modified_count > 0:
                user_updates += 1
                
        elif cat["owner_type"] == "household":
            result = db.households.update_one(
                {"_id": cat["owner_id"]},
                {"$addToSet": {"categories": embedded_cat}}
            )
            if result.modified_count > 0:
                household_updates += 1
                
    print(f"Migrated {user_updates} categories to users.")
    print(f"Migrated {household_updates} categories to households.")
    
    if len(categories) == user_updates + household_updates or len(categories) == 0:
        print("Migration complete. Dropping categories collection...")
        db.categories.drop()
        print("Dropped categories collection.")
    else:
        print("Warning: Not all categories were migrated or they were already migrated. Collection not dropped.")

if __name__ == "__main__":
    migrate_categories()
