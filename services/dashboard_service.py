from datetime import datetime
from db import get_connection


def get_executive_summary(user_id):
    """
    zwraca łączny budżet, łączne wydatki i pozostałą kwotę dla danego użytkownika
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(Amount), 0)
        FROM Budget
        WHERE User_id = %s
    """, (user_id,))
    total_budget = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT COALESCE(SUM(t.Amount), 0)
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
          AND c.Category_type = 'expenses'
    """, (user_id,))
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
def get_detailed_budgets(user_id, month=None, year=None):
        """
        zwraca szczegółowe informacje o budżetach dla danego użytkownika - tabela na dashboardzie z danego miesiaca i roku
        """
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
            AND MONTH(t.Transaction_date) = b.Budget_month
            AND YEAR(t.Transaction_date) = b.Budget_year
        WHERE b.User_id = %s
          AND b.Budget_month = %s
          AND b.Budget_year = %s
        GROUP BY b.Budget_id, c.Category_name, b.Amount
        ORDER BY c.Category_name
    """, (user_id, month, year))

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
        """
        zwraca transakcje dla danego użytkownika, opcjonalnie filtrowane po zakresie dat
         - dane do eksploratora transakcji na dashboardzie
         - jeśli start_date i end_date
        """
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


def get_expenditure_analysis(user_id, month, year):
    """
    zwraca dane do analizy wydatków dla danego użytkownika w danym miesiącu i roku - dane do wykresu na dashboardzie
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
    """, (user_id, month, year))

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