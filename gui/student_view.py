# student_view.py

import sqlite3
from database.db_handler import get_connection


def list_students():
    """
    Fetch all registered students from the database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name, registered_at FROM students")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[INFO] No students registered yet.")
        return []

    print("\n=== Registered Students ===")
    for row in rows:
        sid, name, reg_time = row
        print(f"ID: {sid} | Name: {name} | Registered At: {reg_time}")

    return rows


def view_student(student_id: str):
    """
    Fetch and display details of a single student.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name, registered_at FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if student:
        sid, name, reg_time = student
        print("\n=== Student Details ===")
        print(f"ID: {sid}")
        print(f"Name: {name}")
        print(f"Registered At: {reg_time}")
        return student
    else:
        print(f"[INFO] No student found with ID {student_id}")
        return None


# Example usage
if __name__ == "__main__":
    students = list_students()
    if students:
        sid = input("\nEnter a student ID to view details: ")
        view_student(sid)
