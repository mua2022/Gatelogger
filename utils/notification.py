import os
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# ============ CONFIG ============
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets["EMAIL_ADDRESS"]      
SENDER_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"] 
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
def notify_student_on_login(student_id, student_name):
    """ Notify student via email on successful login."""
    subject = "Login Successful"
    message = f"""
    <h3>Hello {student_name},</h3>
    <p>You have successfully logged in to the Student Attendance System.</p>
    <br>
    <p>Best Regards,<br>Student Attendance System</p>
    """
    send_email(st.secrets["EMAIL_ADDRESS"], subject, message, html=True)
