import bcrypt
from db import get_connection


def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT User_id, Username, Pass
        FROM Users
        WHERE Username = %s
    """, (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def username_exists(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT User_id FROM Users WHERE Username = %s", (username,))
    existing_user = cursor.fetchone()

    cursor.close()
    conn.close()

    return existing_user is not None


def create_user(username, password):
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Users (Username, Pass)
        VALUES (%s, %s)
    """, (username, hashed_password))
    conn.commit()

    cursor.close()
    conn.close()


def verify_user_login(username, password):
    user = get_user_by_username(username)

    if not user:
        return None

    user_id = user[0]
    db_username = user[1]
    stored_hash = user[2]

    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        return {
            "user_id": user_id,
            "username": db_username,
            "role": "ADMIN"
        }

    return None