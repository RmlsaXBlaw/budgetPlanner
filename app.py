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



if __name__ == '__main__':
    app.run(debug=True)