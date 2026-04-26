from db import get_connection
from bson.objectid import ObjectId

def add_category(user_id, household_id, category_name, category_type, scope):
    db = get_connection()

    if scope == 'individual' or not household_id:
        owner_type = 'user'
        owner_id = ObjectId(user_id)
    else:
        owner_type = 'household'
        owner_id = ObjectId(household_id)

    db.categories.insert_one({
        "owner_type": owner_type,
        "owner_id": owner_id,
        "name": category_name,
        "type": category_type
    })