import os
import pyodbc

def get_connection():
    return pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))

def fetch_all_jobs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT job_id, required_skills
        FROM JobListings
    """)

    jobs = cursor.fetchall()

    cursor.close()
    conn.close()

    return jobs
