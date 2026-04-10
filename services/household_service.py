from db import get_connection


def get_household_by_user(user_id):
    """
    Pobiera informacje o gospodarstwie domowym użytkownika.
    Jeśli użytkownik nie należy do żadnego gospodarstwa, zwraca None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT h.Household_id, h.Household_name
        FROM Users u
        JOIN Household h ON u.Household_id = h.Household_id
        WHERE u.User_id = %s
    """, (user_id,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        "household_id": row[0],
        "household_name": row[1]
    }


def update_household_name(household_id, new_name):
    """
    Zmienia nazwę gospodarstwa domowego
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Household
        SET Household_name = %s
        WHERE Household_id = %s
    """, (new_name, household_id))

    conn.commit()
    cursor.close()
    conn.close()


def get_household_members(household_id):
    """
    pobiera listę członków gospodarstwa domowego wraz z ich rolami (member/admin)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT User_id, Username, User_status
        FROM Users
        WHERE Household_id = %s
        ORDER BY Username
    """, (household_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "user_id": row[0],
            "username": row[1],
            "user_status": row[2]
        })

    return result


def add_user_to_household(user_id, household_id, user_status='member'):
    """
    Przypisuje użytkownika do gospodarstwa domowego domyślnie nadaje status 'member'
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Users
        SET Household_id = %s,
            User_status = %s
        WHERE User_id = %s
    """, (household_id, user_status, user_id))

    conn.commit()
    cursor.close()
    conn.close()


def remove_user_from_household(user_id):
    """
    usuwa użytkownika z gospodarstwa domowego zerując jego Household_id i User_status
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Users
        SET Household_id = NULL,
            User_status = NULL
        WHERE User_id = %s
    """, (user_id,))

    conn.commit()
    cursor.close()
    conn.close()


def update_user_household_role(user_id, new_role):
    """
    zmienia role uzytkownika w gospodarstwie domowym (mebmer/admin)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Users
        SET User_status = %s
        WHERE User_id = %s
    """, (new_role, user_id))

    conn.commit()
    cursor.close()
    conn.close()