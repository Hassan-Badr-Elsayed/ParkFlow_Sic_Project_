import math
from datetime import datetime

from core.exceptions import SlotOccupiedError, SlotEmptyError, ReservationError
from core.validators import normalize_plate, validate_vehicle_type


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def _looks_like_email(value):
    return isinstance(value, str) and "@" in value


class Vehicle:
    def __init__(self, plate, vehicle_type):
        self.plate = normalize_plate(plate)
        self.vehicle_type = validate_vehicle_type(vehicle_type)

    def hourly_rate(self):
        rates = {"car": 10.0, "motorcycle": 5.0, "truck": 20.0}
        return rates.get(self.vehicle_type, 10.0)


class Car(Vehicle):
    def __init__(self, plate):
        super().__init__(plate, "car")


class Motorcycle(Vehicle):
    def __init__(self, plate):
        super().__init__(plate, "motorcycle")


class Truck(Vehicle):
    def __init__(self, plate):
        super().__init__(plate, "truck")


class User:
    def __init__(
        self,
        user_id,
        username=None,
        role="customer",
        email="",
        password="",
        has_history=False,
        phone=""
    ):
        if username is None:
            username = user_id
        self.user_id = str(user_id)
        self.username = str(username)
        self.role = role
        self.email = email or "",
        self.phone = phone or ""
        self.password = password if password not in (None, "") else str(self.username)
        self.has_history = _truthy(has_history)

    @property
    def is_returning(self):
        return bool(self.has_history)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "has_history": self.has_history,
            "password": self.password,
        }


class Admin(User):
    def __init__(self, user_id, username="", email="", password=""):
        # Admin("admin", "root") -> username, password
        # Admin("1", "boss", "admin@test.com") -> user_id, username, email
        if email or password:
            super().__init__(
                user_id, username or user_id, "admin", email, password, False
            )
        elif username != "":
            super().__init__(user_id, str(user_id), "admin", "", username, False)
        else:
            super().__init__(user_id, user_id, "admin", "", "", False)


class Employee(User):
    def __init__(self, user_id, username="", email="", password=""):
        if email or password:
            super().__init__(
                user_id, username or user_id, "employee", email, password, False
            )
        elif username != "":
            super().__init__(user_id, str(user_id), "employee", "", username, False)
        else:
            super().__init__(user_id, user_id, "employee", "", "", False)


class Customer(User):
    def __init__(
        self, user_id, username="", email="", has_history=False, password="",plates=None,phone=""
    ):
        # Customer("omar", "pw2") -> username, password
        # Customer("3", "cust_sarah", "sarah@gmail.com", True) -> S1 style
        if email or password or _looks_like_email(username):
            super().__init__(
                user_id,
                username or user_id,
                "customer",
                email,
                password,
                has_history,
                phone
            )
        elif username != "" and not _truthy(has_history):
            super().__init__(user_id, str(user_id), "customer", "", username, False)
        else:
            super().__init__(
                user_id,
                username or user_id,
                "customer",
                email,
                password,
                has_history,
                phone
            )

        self.plates = plates if plates is not None else []
    def to_dict(self):
        data = super().to_dict()
        data["plates"] = ",".join(self.plates) if self.plates else ""
        return data

class ParkingSpace:
    def __init__(self, floor, slot, space_id=None):
        self.floor = int(floor)
        self.slot = int(slot)
        self.space_id = space_id if space_id is not None else f"{self.floor}-{self.slot}"
        self.occupied_by = None
        self.reserved_by = None

    @property
    def status(self):
        if self.occupied_by is not None:
            return "occupied"
        if self.reserved_by is not None:
            return "reserved"
        return "free"

    @status.setter
    def status(self, value):
        value = str(value).strip().lower()
        if value == "free":
            self.occupied_by = None
            self.reserved_by = None
        elif value == "reserved":
            if self.occupied_by is not None:
                raise ReservationError("Cannot reserve an occupied space.")
            if self.reserved_by is None:
                self.reserved_by = ""
        elif value == "occupied":
            if self.occupied_by is None:
                self.occupied_by = self.reserved_by or ""
            self.reserved_by = None
        else:
            raise ReservationError(f"Unknown space status: {value}")

    def occupy(self, session_id):
        if self.occupied_by is not None:
            raise SlotOccupiedError(self.floor, self.slot)
        self.occupied_by = session_id
        self.reserved_by = None

    def reserve(self, plate):
        if not self.is_free():
            raise ReservationError("Space is not free.")
        if self.reserved_by is not None:
            raise ReservationError("Space is already reserved.")
        self.reserved_by = plate
        return self

    def release(self):
        if self.occupied_by is None:
            raise SlotEmptyError(self.floor, self.slot)
        val = self.occupied_by
        self.occupied_by = None
        self.reserved_by = None
        return val

    def clear_reservation(self):
        self.reserved_by = None

    def is_free(self):
        return self.occupied_by is None and self.reserved_by is None

    def to_dict(self):
        return {
            "floor": self.floor,
            "slot": self.slot,
            "space_id": self.space_id,
            "status": self.status,
            "occupied_by": self.occupied_by,
            "reserved_by": self.reserved_by,
        }


class ParkingSession:
    def __init__(
        self,
        session_id,
        plate,
        vehicle_type,
        floor,
        slot,
        entry_time=None,
        exit_time=None,
        fee=0.0,
    ):
        self.session_id = str(session_id)
        self.plate = normalize_plate(plate)
        self.vehicle_type = validate_vehicle_type(vehicle_type)
        self.floor = int(floor)
        self.slot = int(slot)

        if entry_time is None:
            self.entry_time = datetime.now()
        elif isinstance(entry_time, str):
            self.entry_time = datetime.fromisoformat(entry_time) if entry_time else datetime.now()
        else:
            self.entry_time = entry_time

        if exit_time in (None, ""):
            self.exit_time = None
        elif isinstance(exit_time, str):
            self.exit_time = datetime.fromisoformat(exit_time)
        else:
            self.exit_time = exit_time

        self.fee = float(fee) if fee not in (None, "") else 0.0

    @property
    def space_id(self):
        return f"{self.floor}-{self.slot}"

    def close(self, now=None):
        if now is None:
            now = datetime.now()
        elif isinstance(now, str):
            now = datetime.fromisoformat(now)

        self.exit_time = now
        duration_seconds = (self.exit_time - self.entry_time).total_seconds()

        if duration_seconds < 0:
            self.fee = 0.0
            return self.fee

        hours = math.ceil(duration_seconds / 3600.0)
        if hours == 0:
            hours = 1

        dummy_v = Vehicle(self.plate, self.vehicle_type)
        self.fee = hours * dummy_v.hourly_rate()
        return self.fee

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "plate": self.plate,
            "vehicle_type": self.vehicle_type,
            "floor": self.floor,
            "slot": self.slot,
            "space_id": self.space_id,
            "entry_time": self.entry_time.isoformat() if self.entry_time else "",
            "exit_time": self.exit_time.isoformat() if self.exit_time else "",
            "fee": self.fee,
        }

    @classmethod
    def from_dict(cls, data):
        floor = data.get("floor")
        slot = data.get("slot")
        space_id = data.get("space_id")
        if (floor in (None, "") or slot in (None, "")) and space_id:
            parts = str(space_id).replace("_", "-").split("-")
            if len(parts) >= 2:
                floor_part, slot_part = parts[0], parts[-1]
                if floor_part.isalpha():
                    floor = ord(floor_part.upper()[0]) - ord("A")
                else:
                    floor = floor_part
                slot = slot_part
        return cls(
            session_id=data.get("session_id"),
            plate=data.get("plate"),
            vehicle_type=data.get("vehicle_type"),
            floor=floor,
            slot=slot,
            entry_time=data.get("entry_time"),
            exit_time=data.get("exit_time"),
            fee=data.get("fee", 0.0),
        )


def build_grid(floors=3, slots_per_floor=10):
    grid = []
    for f in range(floors):
        floor_spaces = []
        for s in range(slots_per_floor):
            floor_spaces.append(ParkingSpace(f, s))
        grid.append(floor_spaces)
    return grid
