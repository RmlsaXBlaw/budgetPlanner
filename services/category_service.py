from db import get_connection

def add_category(user_id, household_id, category_name, category_type, scope):
    
    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        cursor.execute("""
            INSERT INTO Category (Household_id, User_id, Category_name, Category_type)
            VALUES (NULL, %s, %s, %s)
        """, (user_id, category_name, category_type))
    else:
        # If household scope is selected but user has no household, fallback to individual
        if household_id is None:
            cursor.execute("""
                INSERT INTO Category (Household_id, User_id, Category_name, Category_type)
                VALUES (NULL, %s, %s, %s)
            """, (user_id, category_name, category_type))
        else:
            cursor.execute("""
                INSERT INTO Category (Household_id, User_id, Category_name, Category_type)
                VALUES (%s, NULL, %s, %s)
            """, (household_id, category_name, category_type))

    conn.commit()
    cursor.close()
    conn.close()