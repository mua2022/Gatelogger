# utils/time_utils.py

from datetime import datetime, timedelta


def get_current_time():
    """
    Returns the current system time in formatted string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_time(timestamp: str):
    """
    Convert timestamp string back into datetime object.

    Args:
        timestamp (str): Example "2025-08-21 14:35:00"
    """
    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")


def calculate_duration(login_time: str, logout_time: str):
    """
    Calculate the duration between login and logout in minutes.

    Args:
        login_time (str): Login timestamp
        logout_time (str): Logout timestamp
    """
    login = parse_time(login_time)
    logout = parse_time(logout_time)
    duration = logout - login
    return int(duration.total_seconds() / 60)  # return in minutes


def is_late(checkin_time: str, threshold_hour: int = 9):
    """
    Check if student logged in late.

    Args:
        checkin_time (str): Timestamp string
        threshold_hour (int): Allowed hour to arrive (default 9 AM)
    """
    time = parse_time(checkin_time)
    return time.hour >= threshold_hour


def format_duration(minutes: int):
    """
    Convert minutes into 'Xh Ym' format.
    """
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


# Example usage
if __name__ == "__main__":
    now = get_current_time()
    print("[INFO] Current Time:", now)

    # Simulate login/logout
    login = "2025-08-21 08:45:00"
    logout = "2025-08-21 12:15:00"

    print("[INFO] Duration:", format_duration(calculate_duration(login, logout)))
    print("[INFO] Was Late?:", is_late(login))
