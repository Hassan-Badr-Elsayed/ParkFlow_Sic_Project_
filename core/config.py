import os

FLOORS = 3
SLOTS_PER_FLOOR = 10
MAX_WAITING = 10

PLATE_PATTERN = r'^[A-Z0-9]{3,8}$'

VEHICLE_RATES = {
    'car': 10.0,
    'motorcycle': 5.0,
    'truck': 20.0
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SESSIONS_CSV = os.path.join(DATA_DIR, 'sessions.csv')
PARKED_CSV = os.path.join(DATA_DIR, 'parked.csv')
WAITING_CSV = os.path.join(DATA_DIR, 'waiting.csv')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')

SESSION_FIELDS = ['session_id', 'plate', 'vehicle_type', 'floor', 'slot', 'entry_time', 'exit_time', 'fee']
PARKED_FIELDS = ['session_id', 'plate', 'vehicle_type', 'floor', 'slot', 'entry_time']
WAITING_FIELDS = ['plate', 'vehicle_type', 'join_time']
USER_FIELDS = ['user_id', 'username', 'role', 'email', 'has_history', 'password', 'plates', 'phone']