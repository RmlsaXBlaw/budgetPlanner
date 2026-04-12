from datetime import datetime
from db import get_connection


def get_executive_summary(user_id, household_id=None, month=None, year=None, scope='individual'):
    """
    Returns total budget, total spent, and remaining amount, filtered by scope, month, and year.
    """
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        cursor.execute("""
            SELECT COALESCE(SUM(Amount), 0)
            FROM Budget
            WHERE User_id = %s
              AND Budget_month = %s
              AND Budget_year = %s
        """, (user_id, month, year))
        total_budget = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(t.Amount), 0)
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.User_id = %s
              AND MONTH(t.Transaction_date) = %s
              AND YEAR(t.Transaction_date) = %s
              AND c.Category_type = 'expenses'
        """, (user_id, month, year))
        total_spent = float(cursor.fetchone()[0])

    else:  # household
        if not household_id:
            cursor.close()
            conn.close()
            return {"total_budget": 0.0, "total_spent": 0.0, "total_remaining": 0.0}

        cursor.execute("""
            SELECT COALESCE(SUM(Amount), 0)
            FROM Budget
            WHERE Household_id = %s
              AND Budget_month = %s
              AND Budget_year = %s
        """, (household_id, month, year))
        total_budget = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(t.Amount), 0)
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.Household_id = %s
              AND MONTH(t.Transaction_date) = %s
              AND YEAR(t.Transaction_date) = %s
              AND c.Category_type = 'expenses'
        """, (household_id, month, year))
        total_spent = float(cursor.fetchone()[0])

    cursor.close()
    conn.close()

    return {
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent
    }


# def get_detailed_budgets(user_id):
#     """
#     zwraca szczegółowe informacje o budżetach dla danego użytkownika - tabela na dashboardzie z całego okresu z bazy danych
#     """

#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT
#             c.Category_name AS category_name,
#             'INDIVIDUAL' AS scope,
#             b.Amount AS amount,
#             COALESCE(SUM(t.Amount), 0) AS spent
#         FROM Budget b
#         JOIN Category c ON b.Category_id = c.Category_id
#         LEFT JOIN Transactions t
#             ON t.Category_id = b.Category_id
#             AND t.User_id = b.User_id
#         WHERE b.User_id = %s
#         GROUP BY b.Budget_id, c.Category_name, b.Amount
#         ORDER BY c.Category_name
#     """, (user_id,))

#     rows = cursor.fetchall()

#     cursor.close()
#     conn.close()

#     result = []
#     for row in rows:
#         result.append({
#             "category_name": row[0],
#             "scope": row[1],
#             "amount": float(row[2]),
#             "spent": float(row[3])
#         })

#     return result
def get_detailed_budgets(user_id, household_id=None, month=None, year=None, scope='individual'):
    """
    Returns detailed budgets, filtered by individual or household scope.
    """
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        query = """
            SELECT
                c.Category_name AS category_name,
                'INDIVIDUAL' AS scope,
                b.Amount AS amount,
                COALESCE(SUM(t.Amount), 0) AS spent
            FROM Budget b
            JOIN Category c ON b.Category_id = c.Category_id
            LEFT JOIN Transactions t
                ON t.Category_id = b.Category_id
                AND t.User_id = b.User_id
                AND MONTH(t.Transaction_date) = %s
                AND YEAR(t.Transaction_date) = %s
            WHERE b.User_id = %s
              AND b.Budget_month = %s
              AND b.Budget_year = %s
            GROUP BY b.Budget_id, c.Category_name, b.Amount
            ORDER BY c.Category_name
        """
        params = (month, year, user_id, month, year)

    else:
        if not household_id:
            return []

        query = """
            SELECT
                c.Category_name AS category_name,
                'HOUSEHOLD' AS scope,
                b.Amount AS amount,
                COALESCE(SUM(t.Amount), 0) AS spent
            FROM Budget b
            JOIN Category c ON b.Category_id = c.Category_id
            LEFT JOIN Transactions t
                ON t.Category_id = b.Category_id
                AND t.Household_id = b.Household_id
                AND MONTH(t.Transaction_date) = %s
                AND YEAR(t.Transaction_date) = %s
            WHERE b.Household_id = %s
              AND b.Budget_month = %s
              AND b.Budget_year = %s
            GROUP BY b.Budget_id, c.Category_name, b.Amount
            ORDER BY c.Category_name
        """
        params = (month, year, household_id, month, year)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "category_name": row[0],
            "scope": row[1],
            "amount": float(row[2]),
            "spent": float(row[3])
        })
    return result
    
def get_transactions(user_id, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()

    if start_date and end_date:
        cursor.execute("""
            SELECT
                t.Transaction_id,
                t.Transaction_date,
                t.Amount,
                t.Transaction_desc,
                c.Category_name,
                c.Category_type
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.User_id = %s
              AND t.Transaction_date BETWEEN %s AND %s
            ORDER BY t.Transaction_date DESC, t.Transaction_id DESC
        """, (user_id, start_date, end_date))
    else:
        cursor.execute("""
            SELECT
                t.Transaction_id,
                t.Transaction_date,
                t.Amount,
                t.Transaction_desc,
                c.Category_name,
                c.Category_type
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.User_id = %s
            ORDER BY t.Transaction_date DESC, t.Transaction_id DESC
        """, (user_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "transaction_id": row[0],
            "transaction_date": str(row[1]),
            "amount": float(row[2]),
            "description": row[3],
            "category": row[4],
            "category_type": row[5]
        })

    return result


def get_expenditure_analysis(user_id, household_id, month, year, scope='individual'):
    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        query = """
            SELECT
                c.Category_name,
                COALESCE(SUM(t.Amount), 0) AS spent
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.User_id = %s
              AND MONTH(t.Transaction_date) = %s
              AND YEAR(t.Transaction_date) = %s
              AND c.Category_type = 'expenses'
            GROUP BY c.Category_id, c.Category_name
            ORDER BY spent DESC
        """
        params = (user_id, month, year)
    else:
        if not household_id:
            return []
        query = """
            SELECT
                c.Category_name,
                COALESCE(SUM(t.Amount), 0) AS spent
            FROM Transactions t
            JOIN Category c ON t.Category_id = c.Category_id
            WHERE t.Household_id = %s
              AND MONTH(t.Transaction_date) = %s
              AND YEAR(t.Transaction_date) = %s
              AND c.Category_type = 'expenses'
            GROUP BY c.Category_id, c.Category_name
            ORDER BY spent DESC
        """
        params = (household_id, month, year)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "category_name": row[0],
            "spent": float(row[1])
        })
    return result