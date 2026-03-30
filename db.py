import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Katarzyna090@",
        database="budget_planner"
    )