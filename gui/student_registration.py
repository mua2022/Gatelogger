# student_registration.py

import os
import cv2
import sqlite3
from database.db_handler import init_db, get_connection
from utils.time_utils import get_current_time


DATASET_DIR = "dataset"


def register_student(student_id: str, name: str, capture_images: bool = True, num_samples: int = 20):
    """
    Registers a new student:
      1. Inserts details into database
      2. Captures face dataset from webcam
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if student already exists
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    if cursor.fetchone():
        print(f"[INFO] Student with ID {student_id} already exists.")
        conn.close()
        return False

    # Insert student into DB
    cursor.execute("INSERT INTO students (student_id, name, registered_at) VALUES (?, ?, ?)",
                   (student_id, name, get_current_time()))
    conn.commit()
    conn.close()
    print(f"[INFO] Student {name} ({student_id}) registered in database.")

    # Create dataset folder
    student_folder = os.path.join(DATASET_DIR, student_id)
    os.makedirs(student_folder, exist_ok=True)

    if capture_images:
        capture_face_images(student_id, student_folder, num_samples)

    return True


def capture_face_images(student_id: str, save_dir: str, num_samples: int = 20):
    """
    Capture face images from webcam for training dataset.
    """
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("[INFO] Starting face capture. Look at the camera...")

    count = 0
    while True:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y + h, x:x + w]
            file_path = os.path.join(save_dir, f"{str(count)}.jpg")
            cv2.imwrite(file_path, face_img)

            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imshow('Registering Face', img)

        # Stop if 'q' is pressed or enough samples collected
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
        elif count >= num_samples:
            break

    print(f"[INFO] {count} face samples collected for {student_id}")
    cam.release()
    cv2.destroyAllWindows()


# Example usage
if __name__ == "__main__":
    init_db()
    sid = input("Enter Student ID: ")
    name = input("Enter Student Name: ")
    register_student(sid, name)
