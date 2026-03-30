from flask import Flask, request, render_template, jsonify
from db import get_connection
#request enable form handling
#render_template enable rendering html templates

app = Flask(__name__) #create flask app

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, request received"
    return render_template('loginForm.html')

@app.route('/registration', methods=['GET', 'POST']) 
def registration():
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, request received"
    return render_template('regForm.html')

# ---------------- DASHBOARD ----------------

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # suma przychodów i wydatków
    cursor.execute("""
        SELECT c.Category_type, SUM(t.Amount) AS total
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
        GROUP BY c.Category_type
    """, (user_id,))
    summary = cursor.fetchall()

    # ostatnie 5  transakcji
    cursor.execute("""
        SELECT t.Transaction_id, t.Amount, t.Transaction_date,
               c.Category_name
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
        ORDER BY t.Transaction_date DESC
        LIMIT 5
    """, (user_id,))
    transactions = cursor.fetchall()

    conn.close()

    return jsonify({
        "summary": summary,
        "recent_transactions": transactions
    })

# ---------------- CATEGORY ----------------

# lista kategori
@app.route('/categories/<int:user_id>')
def get_categories(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Category_id, Category_name, Category_type
        FROM Category
        WHERE User_id = %s
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# dodanie kategorii
@app.route('/category/add', methods=['POST'])
def add_category():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Category (Household_id, User_id, Category_name, Category_type)
        VALUES (NULL, %s, %s, %s)
    """, (data['user_id'], data['name'], data['type']))

    conn.commit()
    conn.close()

    return jsonify({"message": "Category added"})

# ---------------- TRANSACTIONS ----------------

@app.route('/transactions/<int:user_id>')
def get_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.Transaction_id,
               t.Amount,
               t.Transaction_date,
               t.Transaction_desc,
               c.Category_name
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
        ORDER BY t.Transaction_date DESC
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/transaction/add', methods=['POST'])
def add_transaction():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()

    if data['scope'] == 'private':
        cursor.execute("""
            INSERT INTO Transactions 
            (Household_id, User_id, Category_id, Amount, Transaction_date, Transaction_desc)
            VALUES (NULL, %s, %s, %s, %s, %s)
        """, (
            data['user_id'],
            data['category_id'],
            data['amount'],
            data['date'],
            data.get('desc')
        ))

    else:  # shared
        cursor.execute("""
            INSERT INTO Transactions 
            (Household_id, User_id, Category_id, Amount, Transaction_date, Transaction_desc)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['household_id'],
            data['user_id'],
            data['category_id'],
            data['amount'],
            data['date'],
            data.get('desc')
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added"})


# ---------------- BUDGET ----------------

@app.route('/budgets/<int:user_id>')
def get_budgets(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.Budget_id,
               b.Budget_month,
               b.Budget_year,
               b.Amount,
               c.Category_name
        FROM Budget b
        JOIN Category c ON b.Category_id = c.Category_id
        WHERE b.User_id = %s
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/budget/add', methods=['POST'])
def add_budget():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Budget 
        (Household_id, User_id, Category_id, Budget_month, Budget_year, Amount)
        VALUES (NULL, %s, %s, %s, %s, %s)
    """, (
        data['user_id'],
        data['category_id'],
        data['month'],
        data['year'],
        data['amount']
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Budget added"})



# ---------------- EXECUTIVE SUMMARY ----------------
# Total Budget, Total Spent, Remaining

@app.route('/executive-summary/<int:user_id>')
def executive_summary(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # total budget
    cursor.execute("""
        SELECT COALESCE(SUM(Amount), 0)
        FROM Budget
        WHERE User_id = %s
    """, (user_id,))
    total_budget = cursor.fetchone()[0]

    # total spent
    cursor.execute("""
        SELECT COALESCE(SUM(t.Amount), 0)
        FROM Transactions t
        JOIN Category c ON t.Category_id = c.Category_id
        WHERE t.User_id = %s
          AND c.Category_type = 'expenses'
    """, (user_id,))
    total_spent = cursor.fetchone()[0]

    remaining = float(total_budget) - float(total_spent)

    conn.close()

    return jsonify({
        "total_budget": float(total_budget),
        "total_spent": float(total_spent),
        "remaining": remaining
    })

# ---------------- EXPENDITURE ANALYSIS ----------------
# dane do wykresu: wydatki wg kategorii

@app.route('/expenditure-analysis/<int:user_id>/<int:month>/<int:year>')
def expenditure_analysis(user_id, month, year):
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
    conn.close()

    data = []
    for row in rows:
        data.append({
            "category": row[0],
            "spent": float(row[1])
        })

    return jsonify(data)


# ---------------- DETAILED BUDGETS ----------------
# tabela: Category, Scope, Budget, Spent, Remaining

@app.route('/detailed-budgets/<int:user_id>/<int:month>/<int:year>')
def detailed_budgets(user_id, month, year):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.Category_name AS Category,
            'INDIVIDUAL' AS Scope,
            b.Amount AS Budget,
            COALESCE(SUM(t.Amount), 0) AS Spent,
            b.Amount - COALESCE(SUM(t.Amount), 0) AS Remaining
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
    conn.close()

    data = []
    for row in rows:
        data.append({
            "Category": row[0],
            "Scope": row[1],
            "Budget": float(row[2]),
            "Spent": float(row[3]),
            "Remaining": float(row[4])
        })

    return jsonify(data)


# ---------------- DATABASE EXPLORER ----------------
# explorer transakcji po zakresie dat

@app.route('/database-explorer/transactions/<int:user_id>')
def database_explorer_transactions(user_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

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
    conn.close()

    data = []
    for row in rows:
        data.append({
            "Transaction_id": row[0],
            "Transaction_date": str(row[1]),
            "Amount": float(row[2]),
            "Description": row[3],
            "Category": row[4],
            "Category_type": row[5]
        })

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)