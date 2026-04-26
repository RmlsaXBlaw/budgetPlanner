from db import get_connection
from bson.objectid import ObjectId

def create_household(household_name, creator_user_id):
    db = get_connection()
    result = db.households.insert_one({"name": household_name})
    household_id = result.inserted_id
    
    db.users.update_one(
        {"_id": ObjectId(creator_user_id)},
        {"$set": {"household_id": household_id, "user_status": "admin"}}
    )
    return str(household_id)

def get_household_by_user(user_id):
    """
    Pobiera informacje o gospodarstwie domowym użytkownika.
    Jeśli użytkownik nie należy do żadnego gospodarstwa, zwraca None
    """
    db = get_connection()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("household_id"):
        return None
        
    household = db.households.find_one({"_id": user["household_id"]})
    if not household:
        return None

    return {"household_id": str(household["_id"]), "household_name": household["name"]}

def update_household_name(household_id, new_name):
    """
    Zmienia nazwę gospodarstwa domowego
    """
    db = get_connection()
    db.households.update_one({"_id": ObjectId(household_id)}, {"$set": {"name": new_name}})

def get_household_members(household_id):
    """
    pobiera listę członków gospodarstwa domowego wraz z ich rolami (member/admin)
    """
    db = get_connection()
    return [
        {
            "user_id": str(u["_id"]),
            "username": u["username"],
            "user_status": u.get("user_status", "member")
        }
        for u in db.users.find({"household_id": ObjectId(household_id)}).sort("username", 1)
    ]

def add_user_to_household(user_id, household_id, user_status='member'):
    """
    Przypisuje użytkownika do gospodarstwa domowego domyślnie nadaje status 'member'
    """
    db = get_connection()
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"household_id": ObjectId(household_id), "user_status": user_status}}
    )

def remove_user_from_household(user_id):
    """
    usuwa użytkownika z gospodarstwa domowego zerując jego Household_id i User_status
    """
    db = get_connection()
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$unset": {"household_id": "", "user_status": ""}}
    )

def update_user_household_role(user_id, new_role):
    """
    zmienia role uzytkownika w gospodarstwie domowym (mebmer/admin)
    """
    db = get_connection()
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"user_status": new_role}})