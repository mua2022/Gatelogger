import sqlite3
from datetime import datetime
import os

DB_PATH = "database/attendance.db"

def get_connection():
    """Return a connection to the database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database with required tables if not exists."""
    conn = get_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        student_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT,
                        course TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      )''')

    # Attendance logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        name TEXT,
                        status TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id)
                      )''')

    # Notifications log (optional)
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT,
                        message TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id)
                      )''')

    conn.commit()
    conn.close()


def add_student(student_id, name, email, course):
    """Add a new student into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR REPLACE INTO students (student_id, name, email, course) VALUES (?, ?, ?, ?)",
                   (student_id, name, email, course))

    conn.commit()
    conn.close()


def get_students():
    """Return all students."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, name, email, course, created_at FROM students")
    students = cursor.fetchall()

    conn.close()
    return students


def log_attendance(student_id, name, status):
    """Insert login/logout event into attendance table."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO attendance (student_id, name, status, timestamp) VALUES (?, ?, ?, ?)",
                   (student_id, name, status, datetime.now()))

    conn.commit()
    conn.close()


def get_attendance():
    """Return attendance logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, name, status, timestamp FROM attendance ORDER BY timestamp DESC")
    logs = cursor.fetchall()

    conn.close()
    return logs


def save_notification(student_id, message):
    """Save notification record."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO notifications (student_id, message, sent_at) VALUES (?, ?, ?)",
                   (student_id, message, datetime.now()))

    conn.commit()
    conn.close()


def get_student_info_from_db():
    """Return a dict {student_id: name} for training dataset usage."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, name FROM students")
    rows = cursor.fetchall()

    conn.close()
    return {student_id: name for student_id, name in rows}
