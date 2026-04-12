from db import get_connection


def add_transaction(user_id, household_id, category_id, amount, transaction_date, scope, transaction_desc=None):
    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        cursor.execute("""
            INSERT INTO Transactions
            (Household_id, User_id, Category_id, Amount, Transaction_date, Transaction_desc)
            VALUES (NULL, %s, %s, %s, %s, %s)
        """, (user_id, category_id, amount, transaction_date, transaction_desc))

    else:
        cursor.execute("""
            INSERT INTO Transactions
            (Household_id, User_id, Category_id, Amount, Transaction_date, Transaction_desc)
            VALUES (%s, NULL, %s, %s, %s, %s)
        """, (household_id, category_id, amount, transaction_date, transaction_desc))

    conn.commit()
    cursor.close()
    conn.close()


def get_user_categories(user_id, household_id=None, scope=None, category_type=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    base_query = """
        SELECT
            Category_id AS category_id,
            Category_name AS category_name,
            Category_type AS category_type,
            CASE
                WHEN User_id IS NOT NULL THEN 'individual'
                ELSE 'household'
            END AS scope
        FROM Category
        WHERE
    """

    conditions = []
    params = []

    if scope == 'individual':
        conditions.append("(User_id = %s AND Household_id IS NULL)")
        params.append(user_id)

    elif scope == 'household':
        if household_id is None:
            cursor.close()
            conn.close()
            return []
        conditions.append("(Household_id = %s AND User_id IS NULL)")
        params.append(household_id)

    else:
        conditions.append("""
            (
                (User_id = %s AND Household_id IS NULL)
                OR
                (Household_id = %s AND User_id IS NULL)
            )
        """)
        params.extend([user_id, household_id])

    if category_type:
        conditions.append("Category_type = %s")
        params.append(category_type)

    query = base_query + " AND ".join(conditions) + " ORDER BY Category_name"

    cursor.execute(query, params)
    categories = cursor.fetchall()

    cursor.close()
    conn.close()
    return categories