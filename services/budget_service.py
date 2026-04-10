from db import get_connection


def add_budget(user_id, household_id, category_id, amount, budget_month, budget_year, scope):
    """
    Dodaje nowy budzet
    
    scope:
    - 'individual' -> budzet przypisany do użytkownika
    - 'household' -> budzet przypisany do gospodarstwa domowego
    """
    conn = get_connection()
    cursor = conn.cursor()

    if scope == 'individual':
        cursor.execute("""
            INSERT INTO Budget (Household_id, User_id, Category_id, Budget_month, Budget_year, Amount)
            VALUES (NULL, %s, %s, %s, %s, %s)
        """, (user_id, category_id, budget_month, budget_year, amount))
    else:
        cursor.execute("""
            INSERT INTO Budget (Household_id, User_id, Category_id, Budget_month, Budget_year, Amount)
            VALUES (%s, NULL, %s, %s, %s, %s)
        """, (household_id, category_id, budget_month, budget_year, amount))

    conn.commit()
    cursor.close()
    conn.close()


def get_budget_by_id(budget_id):
    """
    pobiera jeden budzet po jego ID
    przydatne przy edycji formularza
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Budget_id, Household_id, User_id, Category_id, Budget_month, Budget_year, Amount
        FROM Budget
        WHERE Budget_id = %s
    """, (budget_id,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        "budget_id": row[0],
        "household_id": row[1],
        "user_id": row[2],
        "category_id": row[3],
        "budget_month": row[4],
        "budget_year": row[5],
        "amount": float(row[6])
    }


def update_budget(budget_id, category_id, amount, budget_month, budget_year):
    """
    aktualizuje istniejacy budzet.
    Zmieniane są:
    - kategoria
    - kwota
    - miesiąc
    - rok
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Budget
        SET Category_id = %s,
            Amount = %s,
            Budget_month = %s,
            Budget_year = %s
        WHERE Budget_id = %s
    """, (category_id, amount, budget_month, budget_year, budget_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_budget(budget_id):
    """
    usuwa budzet po ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Budget
        WHERE Budget_id = %s
    """, (budget_id,))

    conn.commit()
    cursor.close()
    conn.close()


def filter_budgets(user_id, household_id=None, month=None, year=None, scope=None):
    """
    pobiera budzety z mozliwoscia filtrowania
    
    filtry opcjonalne:
    - month
    - year
    - scope ('individual' lub 'household')
    
    jesli scope nie jest podany, pobierane są oba typy budetow
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            b.Budget_id,
            c.Category_name,
            CASE
                WHEN b.User_id IS NOT NULL THEN 'INDIVIDUAL'
                ELSE 'HOUSEHOLD'
            END AS scope,
            b.Budget_month,
            b.Budget_year,
            b.Amount
        FROM Budget b
        JOIN Category c ON b.Category_id = c.Category_id
        WHERE (
            b.User_id = %s
            OR b.Household_id = %s
        )
    """

    params = [user_id, household_id]

    if month:
        query += " AND b.Budget_month = %s"
        params.append(month)

    if year:
        query += " AND b.Budget_year = %s"
        params.append(year)

    if scope == 'individual':
        query += " AND b.User_id IS NOT NULL"
    elif scope == 'household':
        query += " AND b.Household_id IS NOT NULL"

    query += " ORDER BY b.Budget_year DESC, b.Budget_month DESC, c.Category_name"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "budget_id": row[0],
            "category_name": row[1],
            "scope": row[2],
            "budget_month": row[3],
            "budget_year": row[4],
            "amount": float(row[5])
        })

    return result