import os
import pyodbc

def get_connection():
    return pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))

def fetch_resume_skills(resume_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT skill_name
        FROM ResumeSkills
        WHERE resume_id = ?
    """, resume_id)

    skills = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return skills

