# utils/logger.py
import datetime


class Logger:
    @staticmethod
    def log_action(action, details=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}"

        print(log_entry)
