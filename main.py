
import streamlit as st
import os
import pickle
import cv2
import numpy as np
import face_recognition
from deepface import DeepFace
from datetime import datetime

# Internal imports
from database.db_handler import init_db, log_attendance, get_student_info_from_db
from utils.time_utils import determine_status
from utils.notification import notify_student_on_login
from gui.student_registration import register_student, capture_face, upload_faces, save_encodings
from gui.report import generate_report
from gui.student_view import view_students

# -------------------------------
# INITIAL SETUP
# -------------------------------
DB_PATH = "database/attendance.db"
IMG_DIR = "student_images"
ENCODE_FILE = "face_recognizer/encodings.pkl"

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if not os.path.exists(ENCODE_FILE):
    with open(ENCODE_FILE, "wb") as f:
        pickle.dump([], f)

# Initialize database
init_db()

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(page_title="AI Student Recognition System", layout="wide")
st.title("🎓 AI Student Logging System")

# Sidebar menu
menu = st.sidebar.radio(
    "Choose Action",
    [
        "📷 Start Camera",
        "📝 Register Student",
        "🧠 Train Dataset",
        "👨‍🎓 View Students",
        "📄 Generate Report",
        "📬 Upload Memo",
        "🗓 Upload Timetable",
    ],
)

# -------------------------------
# CAMERA RECOGNITION
# -------------------------------
if menu == "📷 Start Camera":
    st.subheader("Live Camera Recognition")

    img_file = st.camera_input("Capture a photo")

    if img_file:
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)

        try:
            result = DeepFace.find(
                img_path=frame,
                db_path=IMG_DIR,
                enforce_detection=False
            )

            if len(result) > 0:
                student_id = os.path.basename(result[0].identity.values[0]).split("_")[0]
                name = os.path.basename(result[0].identity.values[0]).split("_")[1]

                status = determine_status(student_id)
                log_attendance(student_id, name, status)

                if status == "login":
                    notify_student_on_login(student_id, name)

                st.success(f"✅ Recognized: {name} ({student_id}) - {status}")
            else:
                st.error("❌ Unknown face detected")

        except Exception as e:
            st.error(f"Recognition failed: {e}")

# -------------------------------
# REGISTER STUDENT
# -------------------------------
elif menu == "📝 Register Student":
    student = register_student()
    if student:
        student_id, name, email, course = student
        st.write("### Next Step: Capture or Upload Face Images")
        img_paths = []
        tab1, tab2 = st.tabs(["📸 Capture", "📂 Upload"])
        with tab1:
            img_paths += capture_face(student_id, name)
        with tab2:
            img_paths += upload_faces(student_id, name)

        if img_paths:
            if st.button("💾 Save Encodings"):
                save_encodings(student_id, name, email, course, img_paths)

# -------------------------------
# TRAIN DATASET
# -------------------------------
elif menu == "🧠 Train Dataset":
    st.subheader("🧠 Train Face Dataset")

    if st.button("Start Training"):
        if not os.path.exists(IMG_DIR):
            st.error("⚠️ No student images found. Please register students first.")
        else:
            encodings_data = []
            student_info = get_student_info_from_db()

            for file in os.listdir(IMG_DIR):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        student_id = file.split("_")[0]
                        student_name = student_info.get(student_id, "Unknown")

                        image_path = os.path.join(IMG_DIR, file)
                        image = face_recognition.load_image_file(image_path)
                        boxes = face_recognition.face_locations(image)

                        if not boxes:
                            st.warning(f"⚠️ Skipping {file}: no face found.")
                            continue

                        encoding = face_recognition.face_encodings(image, known_face_locations=boxes)
                        if not encoding:
                            st.warning(f"⚠️ Skipping {file}: encoding failed.")
                            continue

                        encodings_data.append({
                            'student_id': student_id,
                            'name': student_name,
                            'encoding': encoding[0]
                        })

                        st.success(f"✅ Trained face for {student_name} ({student_id})")

                    except Exception as e:
                        st.error(f"❌ Error processing {file}: {e}")

            # Save encodings
            with open(ENCODE_FILE, 'wb') as f:
                pickle.dump(encodings_data, f)

            st.info(f"🎉 Training complete! {len(encodings_data)} faces saved.")

# -------------------------------
# VIEW STUDENTS
# -------------------------------
elif menu == "👨‍🎓 View Students":
    view_students()

# -------------------------------
# GENERATE REPORT
# -------------------------------
elif menu == "📄 Generate Report":
    generate_report()

# -------------------------------
# UPLOAD MEMO
# -------------------------------
elif menu == "📬 Upload Memo":
    st.subheader("📬 Upload Memo")
    memo_file = st.file_uploader("Upload Memo (PDF, DOCX)", type=["pdf", "docx"])
    if memo_file:
        save_path = os.path.join("uploads/memos", memo_file.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(memo_file.getbuffer())
        st.success(f"✅ Memo uploaded: {memo_file.name}")

# -------------------------------
# UPLOAD TIMETABLE
# -------------------------------
elif menu == "🗓 Upload Timetable":
    st.subheader("🗓 Upload Timetable")
    timetable_file = st.file_uploader("Upload Timetable (PDF, XLSX)", type=["pdf", "xlsx"])
    if timetable_file:
        save_path = os.path.join("uploads/timetables", timetable_file.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(timetable_file.getbuffer())
        st.success(f"✅ Timetable uploaded: {timetable_file.name}")
