from datetime import datetime
import streamlit as st

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
from core.models import ParkingSession
from core.parking_service import ParkingLot
from core.storage import load_records, load_users, save_records, save_users
from core.validators import normalize_plate, validate_vehicle_type


from core.user_service import UserManager


def _parse_time(value):
    if value in (None, ""):
        return datetime.now()
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return datetime.now()
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now()


def _load_user_manager():
    um = UserManager()
    try:
        users = load_users(USERS_CSV)
        if users:
            um.load_users(users)
    except Exception:
        pass
    return um


def _load_lot():
    lot = ParkingLot()
    

    raw_sessions = []
    try:
        raw_sessions = load_records(SESSIONS_CSV) or []
    except Exception:
        raw_sessions = []

    history = []
    for row in raw_sessions:
        exit_time = (row.get("exit_time") or "").strip()
        if not exit_time:
            continue
        try:
            history.append(ParkingSession.from_dict(row))
        except Exception:
            continue
    if history:
        lot.load_history(history)

    parked_rows = []
    try:
        parked_rows = load_records(PARKED_CSV) or []
    except Exception:
        parked_rows = []

    if not parked_rows:
        parked_rows = [
            row
            for row in raw_sessions
            if not str(row.get("exit_time") or "").strip()
        ]

    for row in parked_rows:
        try:
            plate = normalize_plate(row.get("plate"))
            vehicle_type = validate_vehicle_type(row.get("vehicle_type") or "car")
            floor = int(row.get("floor"))
            slot = int(row.get("slot"))
            entry = _parse_time(row.get("entry_time"))
            session_id = row.get("session_id") or f"{plate}-{entry.isoformat()}"
            session = ParkingSession(
                session_id, plate, vehicle_type, floor, slot, entry, None, 0.0
            )
            space = lot.grid[floor][slot]
            if not space.is_free() or lot._active.contains(plate):
                continue
            space.occupy(plate)
            lot._active.put(plate, session)
        except Exception:
            continue

    waiting_rows = []
    try:
        waiting_rows = load_records(WAITING_CSV) or []
    except Exception:
        waiting_rows = []

    for row in waiting_rows:
        try:
            plate = normalize_plate(row.get("plate"))
            if lot._is_known(plate):
                continue
            vehicle_type = validate_vehicle_type(row.get("vehicle_type") or "car")
            queued_at = _parse_time(row.get("join_time") or row.get("queued_at"))
            lot._waiting.enqueue(
                {"plate": plate, "vehicle_type": vehicle_type, "queued_at": queued_at}
            )
            lot._waiting_plates.add(plate)
        except Exception:
            continue

    return lot, raw_sessions



def init_state():
    if "user_manager" not in st.session_state:
        st.session_state["user_manager"] = _load_user_manager()
    if "lot" not in st.session_state:
        lot, raw_sessions = _load_lot()
        st.session_state["lot"] = lot
        st.session_state["csv_session_rows"] = raw_sessions
        
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
        
    if "csv_session_rows" not in st.session_state:
        st.session_state["csv_session_rows"] = load_records(SESSIONS_CSV) or []

def get_user_manager():
    init_state()
    return st.session_state["user_manager"]


def get_lot():
    init_state()
    return st.session_state["lot"]


def get_current_user():
    init_state()
    return st.session_state.get("current_user")


def set_current_user(user):
    st.session_state["current_user"] = user


def save_all():
    lot = get_lot()
    um = get_user_manager()

    save_users(um.get_users(), USERS_CSV)

    
    from_lot = {str(s.session_id): s.to_dict() for s in lot.get_history()}
    merged = []
    seen = set()
    for row in st.session_state.get("csv_session_rows") or []:
        sid = str(row.get("session_id", ""))
        if sid in from_lot:
            merged.append(_session_csv_row(from_lot[sid]))
            seen.add(sid)
        else:
            merged.append(_session_csv_row(row))
            seen.add(sid)
    for sid, data in from_lot.items():
        if sid not in seen:
            merged.append(_session_csv_row(data))
            seen.add(sid)
    save_records(SESSIONS_CSV, merged, SESSION_FIELDS)
    st.session_state["csv_session_rows"] = merged

    parked = []
    for session in lot.get_active_sessions():
        data = session.to_dict()
        parked.append({field: data.get(field, "") for field in PARKED_FIELDS})
    save_records(PARKED_CSV, parked, PARKED_FIELDS)

    waiting = []
    for item in lot.get_waiting_list():
        queued = item.get("queued_at") or item.get("join_time") or ""
        if hasattr(queued, "isoformat"):
            queued = queued.isoformat()
        waiting.append(
            {
                "plate": item.get("plate", ""),
                "vehicle_type": item.get("vehicle_type", "car"),
                "join_time": queued,
            }
        )
    save_records(WAITING_CSV, waiting, WAITING_FIELDS)


def _session_csv_row(row):
    data = dict(row)
    return {field: data.get(field, "") for field in SESSION_FIELDS}


def analytics_records():
    """Plain list of dicts for core.analytics (CSV rows + live history)."""
    init_state()
    records = []
    seen = set()
    for row in st.session_state.get("csv_session_rows") or []:
        copied = dict(row)
        sid = str(copied.get("session_id", ""))
        records.append(_with_space_id(copied))
        if sid:
            seen.add(sid)
    for session in get_lot().get_history():
        data = session.to_dict()
        sid = str(data.get("session_id", ""))
        if sid and sid in seen:
            continue
        records.append(_with_space_id(data))
        if sid:
            seen.add(sid)
    return records


def _with_space_id(row):
    data = dict(row)
    if not data.get("space_id"):
        try:
            floor = int(data.get("floor", 0))
            slot = int(data.get("slot", 0))
            data["space_id"] = f"{chr(ord('A') + floor)}-{slot:02d}"
        except (TypeError, ValueError):
            data["space_id"] = str(data.get("space_id") or "")
    if not data.get("duration_min"):
        try:
            entry = datetime.fromisoformat(str(data.get("entry_time")))
            exit_time = datetime.fromisoformat(str(data.get("exit_time")))
            data["duration_min"] = (exit_time - entry).total_seconds() / 60.0
        except Exception:
            data["duration_min"] = data.get("duration_min") or ""
    return data