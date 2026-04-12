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



