import bcrypt
from db import get_connection
from bson.objectid import ObjectId


def get_user_by_username(username):
    db = get_connection()
    return db.users.find_one({"username": username})


def username_exists(username):
    db = get_connection()
    return db.users.find_one({"username": username}) is not None


def create_user(username, password):
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    db = get_connection()
    db.users.insert_one({
        "username": username,
        "password": hashed_password,
        "household_id": None,
        "user_status": None
    })


def verify_user_login(username, password):
    user = get_user_by_username(username)

    if not user:
        return None

    if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "role": "ADMIN"
        }

    return None