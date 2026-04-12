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


def get_transaction_by_id(transaction_id):
    """
    Pobiera jedną transakcję po ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Transaction_id, Household_id, User_id, Category_id, Amount, Transaction_date, Transaction_desc
        FROM Transactions
        WHERE Transaction_id = %s
    """, (transaction_id,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        "transaction_id": row[0],
        "household_id": row[1],
        "user_id": row[2],
        "category_id": row[3],
        "amount": float(row[4]),
        "transaction_date": row[5],
        "transaction_desc": row[6]
    }


def update_transaction(transaction_id, category_id, amount, transaction_date, transaction_desc):
    """
    Aktualizuje dane istniejącej transakcji
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Transactions
        SET Category_id = %s,
            Amount = %s,
            Transaction_date = %s,
            Transaction_desc = %s
        WHERE Transaction_id = %s
    """, (category_id, amount, transaction_date, transaction_desc, transaction_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_transaction(transaction_id):
    """
    Usuwa transakcję po ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Transactions
        WHERE Transaction_id = %s
    """, (transaction_id,))

    conn.commit()
    cursor.close()
    conn.close()


def filter_transactions(user_id, household_id=None, start_date=None, end_date=None, category_id=None, min_amount=None, max_amount=None):
    """
    Pobiera transakcje z możliwością filtrowania
    
    Możliwe filtry:
    - data od / do
    - kategoria
    - minimalna kwota
    - maksymalna kwota
    
    Pokazuje transakcje użytkownika oraz gospodarstwa domowego
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            t.Transaction_id,
            c.Category_name,
            t.Amount,
            t.Transaction_date,
            t.Transaction_desc
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE (
            t.User_id = %s
            OR t.Household_id = %s
        )
    """
    params = [user_id, household_id]

    if start_date:
        query += " AND t.Transaction_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND t.Transaction_date <= %s"
        params.append(end_date)

    if category_id:
        query += " AND t.Category_id = %s"
        params.append(category_id)

    if min_amount is not None:
        query += " AND t.Amount >= %s"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND t.Amount <= %s"
        params.append(max_amount)

    query += " ORDER BY t.Transaction_date DESC, t.Transaction_id DESC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "transaction_id": row[0],
            "category_name": row[1],
            "amount": float(row[2]),
            "transaction_date": row[3],
            "transaction_desc": row[4]
        })

    return result


def get_last_user_transactions(user_id, limit=5):
    """
    Zwraca ostatnie 5  transakcji danego użytkownika 
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.Transaction_id,
            c.Category_name,
            t.Amount,
            t.Transaction_date,
            t.Transaction_desc
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
        ORDER BY t.Transaction_date DESC, t.Transaction_id DESC
        LIMIT %s
    """, (user_id, limit))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "transaction_id": row[0],
            "category_name": row[1],
            "amount": float(row[2]),
            "transaction_date": row[3],
            "transaction_desc": row[4]
        })

    return result

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