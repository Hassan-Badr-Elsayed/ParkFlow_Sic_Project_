import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.config import SESSION_FIELDS, SESSIONS_CSV, USER_FIELDS, USERS_CSV

def generate():
    sessions_data = [
        {'session_id': '1', 'plate': 'ABC101', 'vehicle_type': 'car', 'floor': '0', 'slot': '1', 'entry_time': '2026-09-01T08:30:00', 'exit_time': '2026-09-01T10:30:00', 'fee': '20.0'},
        {'session_id': '2', 'plate': 'ABC102', 'vehicle_type': 'motorcycle', 'floor': '1', 'slot': '4', 'entry_time': '2026-09-01T09:00:00', 'exit_time': '2026-09-01T10:00:00', 'fee': '5.0'},
        {'session_id': '3', 'plate': 'ABC103', 'vehicle_type': 'truck', 'floor': '2', 'slot': '0', 'entry_time': '2026-09-01T09:15:00', 'exit_time': '2026-09-01T12:15:00', 'fee': '60.0'},
        {'session_id': '4', 'plate': 'ABC104', 'vehicle_type': 'car', 'floor': '0', 'slot': '2', 'entry_time': '2026-09-01T10:00:00', 'exit_time': '2026-09-01T11:30:00', 'fee': '20.0'},
        {'session_id': '5', 'plate': 'ABC105', 'vehicle_type': 'car', 'floor': '1', 'slot': '1', 'entry_time': '2026-09-01T11:00:00', 'exit_time': '2026-09-01T14:00:00', 'fee': '30.0'},
        {'session_id': '286', 'plate': 'DIRTY01', 'vehicle_type': 'car', 'floor': '0', 'slot': '1', 'entry_time': '2026-09-01T08:00:00', 'exit_time': '', 'fee': '0.0'},
        {'session_id': '291', 'plate': 'INVALID_PLATE_TOO_LONG_123', 'vehicle_type': 'car', 'floor': '0', 'slot': '1', 'entry_time': '2026-09-01T08:00:00', 'exit_time': '2026-09-01T09:00:00', 'fee': '10.0'},
        {'session_id': '296', 'plate': 'NEG001', 'vehicle_type': 'car', 'floor': '0', 'slot': '1', 'entry_time': '2026-09-01T10:00:00', 'exit_time': '2026-09-01T08:00:00', 'fee': '-20.0'}
    ]

    users_data = [
        {'user_id': '1', 'username': 'admin_boss', 'role': 'admin', 'email': 'admin@parkflow.com', 'has_history': 'False'},
        {'user_id': '2', 'username': 'emp_john', 'role': 'employee', 'email': 'john@parkflow.com', 'has_history': 'False'},
        {'user_id': '3', 'username': 'cust_sarah', 'role': 'customer', 'email': 'sarah@gmail.com', 'has_history': 'True'},
        {'user_id': '4', 'username': 'cust_alex', 'role': 'customer', 'email': 'alex@gmail.com', 'has_history': 'False'},
        {'user_id': '5', 'username': 'cust_mona', 'role': 'customer', 'email': 'mona@gmail.com', 'has_history': 'True'}
    ]

    os.makedirs(os.path.dirname(SESSIONS_CSV), exist_ok=True)
    with open(SESSIONS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SESSION_FIELDS)
        writer.writeheader()
        writer.writerows(sessions_data)

    os.makedirs(os.path.dirname(USERS_CSV), exist_ok=True)
    with open(USERS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=USER_FIELDS)
        writer.writeheader()
        writer.writerows(users_data)

    print("CSV files populated successfully.")

if __name__ == '__main__':
    generate()