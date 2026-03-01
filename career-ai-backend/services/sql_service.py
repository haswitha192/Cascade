import os
import pyodbc

def get_connection():
    conn_str = os.getenv("SQL_CONNECTION_STRING")
    return pyodbc.connect(conn_str)


def insert_resume_skills(resume_id: int, skills: list):

    conn = get_connection()
    cursor = conn.cursor()

    for skill in skills:
        cursor.execute("""
            INSERT INTO dbo.ResumeSkills (resume_id, skill_name, confidence_score)
            VALUES (?, ?, ?)
        """, resume_id, skill, 1.0)

    conn.commit()
    cursor.close()
    conn.close()

def insert_resume(user_id: int, blob_url: str, extracted_text: str, resume_score: float):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Resumes 
        (user_id, resume_blob_url, extracted_text, created_at, resume_score)
        OUTPUT INSERTED.resume_id
        VALUES (?, ?, ?, GETDATE(), ?)
    """, user_id, blob_url, extracted_text, resume_score)

    resume_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return resume_id