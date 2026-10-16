import csv
import os

from core.config import (
    PARKED_CSV,
    PARKED_FIELDS,
    SESSION_FIELDS,
    SESSIONS_CSV,
    USER_FIELDS,
    USERS_CSV,
    WAITING_CSV,
    WAITING_FIELDS,
)
from core.models import Admin, Customer, Employee, ParkingSession, User


def save_records(filepath, records, fieldnames):
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            if isinstance(rec, dict):
                writer.writerow(rec)
            elif hasattr(rec, "to_dict"):
                writer.writerow(rec.to_dict())


def load_records(filepath):
    if not filepath or not os.path.exists(filepath):
        return []

    records = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    except Exception:
        return []

    return records


def user_from_dict(row):
    if row is None:
        return None
    role = str(row.get("role", "customer")).strip().lower()
    user_id = row.get("user_id") or row.get("username")
    username = row.get("username") or user_id
    email = row.get("email", "")
    password = row.get("password") or username
    has_history = row.get("has_history", False)

    plates_str = str(row.get("plates", ""))
    plates_list = [p.strip() for p in plates_str.split(",") if p.strip()] if plates_str else []
    phone = str(row.get("phone", ""))
    if role == "admin":
        return Admin(user_id, username=username, email=email, password=password)
    if role == "employee":
        return Employee(user_id, username=username, email=email, password=password)
    if role in ("customer", "driver"):
        return Customer(
            user_id,
            username=username,
            email=email,
            has_history=has_history,
            password=password,
            plates=plates_list,
            phone = phone
        )
    
    return User(
        user_id,
        username,
        role=role or "customer",
        email=email,
        password=password,
        has_history=has_history,
    )


def load_users(filepath=None):
    rows = load_records(filepath or USERS_CSV)
    users = []
    for row in rows:
        try:
            user = user_from_dict(row)
            if user is not None:
                users.append(user)
        except Exception:
            continue
    return users


def save_users(users, filepath=None):
    save_records(filepath or USERS_CSV, users, USER_FIELDS)


def load_sessions(filepath=None):
    rows = load_records(filepath or SESSIONS_CSV)
    sessions = []
    for row in rows:
        try:
            sessions.append(ParkingSession.from_dict(row))
        except Exception:
            continue
    return sessions


def save_sessions(sessions, filepath=None):
    save_records(filepath or SESSIONS_CSV, sessions, SESSION_FIELDS)


def load_parked(filepath=None):
    return load_records(filepath or PARKED_CSV)


def save_parked(sessions, filepath=None):
    rows = []
    for item in sessions:
        data = item.to_dict() if hasattr(item, "to_dict") else dict(item)
        rows.append({k: data.get(k, "") for k in PARKED_FIELDS})
    save_records(filepath or PARKED_CSV, rows, PARKED_FIELDS)


def load_waiting(filepath=None):
    return load_records(filepath or WAITING_CSV)


def save_waiting(waiting, filepath=None):
    rows = []
    for item in waiting:
        data = dict(item)
        queued = data.get("queued_at") or data.get("join_time") or ""
        if hasattr(queued, "isoformat"):
            queued = queued.isoformat()
        rows.append(
            {
                "plate": data.get("plate", ""),
                "vehicle_type": data.get("vehicle_type", "car"),
                "join_time": queued,
            }
        )
    save_records(filepath or WAITING_CSV, rows, WAITING_FIELDS)
