# main.py — Streamlit entrypoint (DeepFace-only, Streamlit Cloud friendly)

import streamlit as st
import os
import io
import pickle
import numpy as np
from PIL import Image
from datetime import datetime, date

from deepface import DeepFace

# Your local modules
from database.db_handler import init_db, insert_student, list_students, log_attendance
from utils.time_utils import determine_status
from utils.notification import notify_student_on_login
from report import build_report_dataframe, export_csv  # adjust if your filenames differ

# ----------------------------
# Paths & bootstrap
# ----------------------------
DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "attendance.db")
IMG_DIR = "student_images"  # DeepFace 'db_path' – each student's images live here

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# optional legacy encodings file path (unused by DeepFace; kept for compatibility)
ENCODE_FILE = "face_recognizer/encodings.pkl"
if not os.path.exists(ENCODE_FILE):
    with open(ENCODE_FILE, "wb") as f:
        pickle.dump([], f)

# initialize database tables
init_db()

# ----------------------------
# Streamlit page config
# ----------------------------
st.set_page_config(page_title="AI Student Logging System", layout="wide")
st.title("🎓 AI Student Logging System (DeepFace)")

# ----------------------------
# Sidebar menu
# ----------------------------
menu = st.sidebar.radio(
    "Choose Action",
    [
        "📷 Start Camera",
        "📝 Register Student",
        "👨‍🎓 View Students",
        "📄 Generate Report",
        "🧰 Database / Images",
        "ℹ️ Help",
    ],
)

# ----------------------------
# Helpers
# ----------------------------
def save_image_bytes_to_student_dir(student_id: str, name: str, file_bytes: bytes, suffix: str = "") -> str:
    """Save raw image bytes into IMG_DIR/{student_id}_{name}/timestamp_suffix.jpg and return path."""
    safe_id = student_id.strip().replace("/", "_")
    safe_name = name.strip().replace("/", "_")
    folder = os.path.join(IMG_DIR, f"{safe_id}_{safe_name}")
    os.makedirs(folder, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{safe_id}_{ts}{suffix}.jpg"
    path = os.path.join(folder, filename)

    with Image.open(io.BytesIO(file_bytes)) as im:
        # ensure RGB JPG
        rgb = im.convert("RGB")
        rgb.save(path, format="JPEG", quality=95)

    return path


def numpy_from_uploaded(uploaded_file) -> np.ndarray:
    """Convert Streamlit UploadedFile to RGB numpy array."""
    image = Image.open(uploaded_file).convert("RGB")
    return np.array(image)  # RGB


def find_best_match_with_deepface(rgb_numpy: np.ndarray, db_path: str):
    """
    Use DeepFace.find to search inside db_path.
    Returns (match_path or None, distance or None, df or None)
    """
    try:
        # DeepFace expects BGR by OpenCV internally, but it accepts numpy RGB as well.
        # We'll pass RGB; DeepFace handles conversions inside.
        results = DeepFace.find(img_path=rgb_numpy, db_path=db_path, enforce_detection=False)

        # DeepFace.find returns a list of DataFrames (one per model/backend). If default model used, it's a list with one DF.
        if isinstance(results, list) and len(results) > 0 and not results[0].empty:
            df = results[0].sort_values(by="distance", ascending=True).reset_index(drop=True)
            best_row = df.iloc[0]
            return best_row.get("identity"), float(best_row.get("distance", np.nan)), df
        else:
            return None, None, None
    except Exception as e:
        st.error(f"DeepFace.find failed: {e}")
        return None, None, None


def parse_student_from_identity_path(identity_path: str):
    """
    Given a path like 'student_images/12345_John Doe/img1.jpg',
    return ('12345', 'John Doe').
    """
    try:
        base = os.path.basename(os.path.dirname(identity_path))  # folder name '12345_John Doe'
        parts = base.split("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, None
    except Exception:
        return None, None


# ----------------------------
# 📷 Start Camera
# ----------------------------
if menu == "📷 Start Camera":
    st.subheader("Live Recognition (Capture a single frame)")
    st.info(
        "Click **'Take Photo'** to capture a frame. "
        "We’ll search for the closest match in your student image database.",
        icon="💡",
    )

    captured = st.camera_input("Capture a photo")
    if captured:
        # Convert to numpy RGB
        img_np = numpy_from_uploaded(captured)

        # Find best match in the DB
        best_identity, distance, df = find_best_match_with_deepface(img_np, IMG_DIR)

        if best_identity:
            student_id, name = parse_student_from_identity_path(best_identity)  # from folder
            if not student_id or not name:
                st.warning("Matched an image, but folder name didn’t follow 'ID_Name' format.")
            else:
                status = determine_status(student_id)
                log_attendance(student_id, name, status)

                if status == "login":
                    notify_student_on_login(student_id, name)

                st.success(f"✅ Recognized: **{name}** ({student_id}) — *{status}*")
                if distance is not None:
                    st.caption(f"Match distance: {distance:.4f}  (lower is closer)")

                with st.expander("Show top matches"):
                    if df is not None:
                        st.dataframe(df[["identity", "distance"]].head(10), use_container_width=True)
        else:
            st.error("❌ No match found. Consider registering this student or adding more images.")


# ----------------------------
# 📝 Register Student
# ----------------------------
elif menu == "📝 Register Student":
    st.subheader("Register a New Student")
    with st.form("register_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("Student ID", help="e.g., SCS/001/2024").strip()
            name = st.text_input("Full Name", help="e.g., Jane Doe").strip()
        with col2:
            email = st.text_input("Email", help="e.g., jane@example.com").strip()
            course = st.text_input("Course", help="e.g., BCSY1S2").strip()

        submitted = st.form_submit_button("Save Student")
        if submitted:
            if not all([student_id, name, email, course]):
                st.error("Please fill all fields.")
            else:
                try:
                    insert_student(student_id, name, email, course)
                    st.success(f"✅ Student saved: {name} ({student_id})")
                    st.session_state["reg_student"] = (student_id, name)
                except Exception as e:
                    st.error(f"Failed to insert student: {e}")

    # Images collection for the just-registered student
    if "reg_student" in st.session_state:
        sid, sname = st.session_state["reg_student"]
        st.markdown("### Add Face Images")
        tab_cap, tab_up = st.tabs(["📸 Capture", "📂 Upload"])

        with tab_cap:
            st.info("Capture 1–5 photos. Click after each capture to save.", icon="📷")
            captured_img = st.camera_input("Capture image")
            if captured_img:
                path = save_image_bytes_to_student_dir(sid, sname, captured_img.getvalue(), suffix="_cap")
                st.success(f"Saved: `{os.path.relpath(path)}`")

        with tab_up:
            files = st.file_uploader(
                "Upload JPG/PNG images",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )
            if files:
                saved_count = 0
                for f in files:
                    try:
                        path = save_image_bytes_to_student_dir(sid, sname, f.getvalue(), suffix="_up")
                        saved_count += 1
                    except Exception as e:
                        st.error(f"Failed to save {f.name}: {e}")
                if saved_count:
                    st.success(f"✅ Saved {saved_count} images to `{IMG_DIR}/{sid}_{sname}/`")

        st.caption(
            "DeepFace doesn’t require a separate training step. "
            "Once images are in the database folder, recognition is ready."
        )


# ----------------------------
# 👨‍🎓 View Students
# ----------------------------
elif menu == "👨‍🎓 View Students":
    st.subheader("Registered Students")
    try:
        df = list_students()  # should return a pandas DataFrame
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load students: {e}")


# ----------------------------
# 📄 Generate Report
# ----------------------------
elif menu == "📄 Generate Report":
    st.subheader("Attendance Report")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Start date", value=date.today())
    with col2:
        end = st.date_input("End date", value=date.today())

    if st.button("Build Report"):
        try:
            df = build_report_dataframe(start, end)  # implement in report.py
            if df is None or df.empty:
                st.warning("No attendance records found for the selected range.")
            else:
                st.success(f"Report rows: {len(df)}")
                st.dataframe(df, use_container_width=True)
                csv_path = export_csv(df, start, end)  # implement in report.py
                st.download_button(
                    "Download CSV",
                    data=open(csv_path, "rb").read(),
                    file_name=os.path.basename(csv_path),
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Failed to build/export report: {e}")


# ----------------------------
# 🧰 Database / Images
# ----------------------------
elif menu == "🧰 Database / Images":
    st.subheader("Image Database Health")
    # Count students and images
    student_dirs = [d for d in os.listdir(IMG_DIR) if os.path.isdir(os.path.join(IMG_DIR, d))]
    total_images = 0
    for d in student_dirs:
        folder = os.path.join(IMG_DIR, d)
        total_images += len([f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))])

    st.write(f"📁 Student folders: **{len(student_dirs)}**")
    st.write(f"🖼 Total images: **{total_images}**")

    st.markdown("**Folder naming rule:** `student_images/<STUDENT_ID>_<FULL_NAME>/image.jpg`")
    st.caption("DeepFace uses these images directly for recognition. No extra training step is required.")

    with st.expander("Show folder contents"):
        for d in sorted(student_dirs):
            folder = os.path.join(IMG_DIR, d)
            imgs = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            st.write(f"- `{d}` — {len(imgs)} images")


# ----------------------------
# ℹ️ Help
# ----------------------------
elif menu == "ℹ️ Help":
    st.subheader("Help & Tips")
    st.markdown(
        """
- Use **Register Student** to add the student to the database and save a few clear face photos.
- Use **Start Camera** to capture a frame and match it against your image database.
- If matches are inconsistent: add more images with different lighting/angles.
- **View Students** shows all registered students and their details.
"""
)