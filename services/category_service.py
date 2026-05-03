from db import get_connection
from bson.objectid import ObjectId

def add_category(user_id, household_id, category_name, category_type, scope):
    db = get_connection()
    
    category_doc = {
        "_id": ObjectId(),
        "name": category_name,
        "type": category_type
    }

    if scope == 'individual' or not household_id:
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"categories": category_doc}}
        )
    else:
        db.households.update_one(
            {"_id": ObjectId(household_id)},
            {"$push": {"categories": category_doc}}
        )

def get_categories_for_user(user_id, household_id=None):
    """
    Returns a unified list of categories for the user and their household (if any).
    Each category includes its scope ('individual' or 'household').
    """
    db = get_connection()
    categories = []

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user and "categories" in user:
        for c in user["categories"]:
            c["scope"] = "individual"
            categories.append(c)

    if household_id:
        household = db.households.find_one({"_id": ObjectId(household_id)})
        if household and "categories" in household:
            for c in household["categories"]:
                c["scope"] = "household"
                categories.append(c)

    return categories