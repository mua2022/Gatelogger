import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# ============ CONFIG ============
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"       # Change this
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")       # Use App Password, not real password!
# ================================


def send_email(receiver_email, subject, message, html=False):
    """
    Send an email notification.

    Args:
        receiver_email (str): Recipient email address
        subject (str): Email subject
        message (str): Message body (plain text or HTML)
        html (bool): If True, send HTML email
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(message, "html"))
        else:
            msg.attach(MIMEText(message, "plain"))

        # Connect to mail server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()

        print(f"[INFO] Email sent successfully to {receiver_email}")

    except Exception as e:
        print(f"[ERROR] Failed to send email to {receiver_email}: {e}")


def send_exam_reminder(receiver_email, exam_name, exam_date):
    """
    Send exam reminder email.
    """
    subject = f"Reminder: Upcoming Exam - {exam_name}"
    message = f"""
    <h3>Dear Student,</h3>
    <p>This is a reminder that you have <b>{exam_name}</b> scheduled on 
    <b>{exam_date}</b>.</p>
    <p>Please be prepared and arrive on time.</p>
    <br>
    <p>Best of luck!</p>
    <p><i>Student Attendance System</i></p>
    """
    send_email(receiver_email, subject, message, html=True)


def send_attendance_summary(receiver_email, student_name, present_days, total_days):
    """
    Send attendance summary email.
    """
    subject = f"Attendance Summary for {student_name}"
    percentage = (present_days / total_days) * 100 if total_days > 0 else 0
    message = f"""
    <h3>Hello {student_name},</h3>
    <p>Here is your attendance summary:</p>
    <ul>
        <li>Present Days: {present_days}</li>
        <li>Total Days: {total_days}</li>
        <li>Attendance Percentage: <b>{percentage:.2f}%</b></li>
    </ul>
    <p>Please ensure your attendance remains above the required threshold.</p>
    <br>
    <p>Best Regards,<br>Student Attendance System</p>
    """
    send_email(receiver_email, subject, message, html=True)


# Example usage
if __name__ == "__main__":
    # Send test reminder
    send_exam_reminder("student_email@example.com", "Computer Science Exam", "2025-09-10")
    # Send test attendance summary
    send_attendance_summary("student_email@example.com", "John Doe", 18, 20)
