from datetime import datetime

from core.config import FLOORS, SLOTS_PER_FLOOR, MAX_WAITING
from core.exceptions import (
    AuthenticationError,
    DuplicateUserError,
    DuplicateVehicleError,
    InvalidStateError,
    NothingToUndoError,
    ReservationError,
    UndoNotAllowedError,
    UserNotFoundError,
    VehicleNotFoundError,
    WaitingListFullError,
)
from core.models import Customer, Employee, ParkingSession, User, build_grid
from core.structures import HashTable, Queue, Stack
from core.validators import normalize_plate, validate_vehicle_type

HASH_SIZE = 53
FLOOR_WEIGHT = 100


def space_distance(floor_index, slot_index):
    return floor_index * FLOOR_WEIGHT + slot_index


class ParkingLot:
    def __init__(
        self, floors=FLOORS, slots_per_floor=SLOTS_PER_FLOOR, max_waiting=MAX_WAITING
    ):
        self.floors = floors
        self.slots_per_floor = slots_per_floor
        self.max_waiting = max_waiting
        self._reset()

    def _reset(self):
        self.grid = build_grid(self.floors, self.slots_per_floor)
        self._waiting = Queue()
        self._waiting_plates = set()
        self._active = HashTable(HASH_SIZE)
        self._actions = Stack()
        self._history = []
        self._users = HashTable(HASH_SIZE)

    @property
    def parking_history(self):
        return self._history

    @staticmethod
    def _now(now):
        return now if now is not None else datetime.now()

    def _is_known(self, plate):
        return self._active.contains(plate) or plate in self._waiting_plates

    def _find_best_space(self):
        best, best_distance = None, None
        for f, row in enumerate(self.grid):
            for s, space in enumerate(row):
                if space.is_free():
                    d = space_distance(f, s)
                    if best_distance is None or d < best_distance:
                        best, best_distance = (f, s), d
        return best

    def _find_reserved_position(self, plate):
        for f, row in enumerate(self.grid):
            for s, space in enumerate(row):
                if space.reserved_by == plate and space.occupied_by is None:
                    return (f, s)
        return None

    def _start_session(self, plate, vehicle_type, position, now):
        f, s = position
        session_id = f"{plate}-{now.isoformat()}"
        session = ParkingSession(session_id, plate, vehicle_type, f, s, now)
        self.grid[f][s].occupy(plate)
        self._active.put(plate, session)
        return session

    def _push_action(self, kind, plate, now, **details):
        entry = {"type": kind, "plate": plate, "time": now.isoformat()}
        entry.update(details)
        self._actions.push(entry)

    def _drain_queue(self):
        return [self._waiting.dequeue() for _ in range(self._waiting.size())]

    def _is_returning_customer(self, user, plate):
        if user is None:
            return False
        if getattr(user, "has_history", False) or getattr(user, "is_returning", False):
            return True
        for session in self._history:
            if session.plate == plate:
                return True
            username = getattr(user, "username", None)
            if username and getattr(session, "username", None) == username:
                return True
        return False

    def reserve_space(self, plate: str, user, now=None) -> dict:
        now = self._now(now)
        from core.validators import normalize_plate
        from core.exceptions import ReservationError
        plate = normalize_plate(plate)

        if user is None:
            raise ReservationError("You must be logged in to reserve a space.")

        role = str(getattr(user, "role", "")).lower()
        if role not in ("customer", "driver"):
            raise ReservationError("Only customers can reserve a space.")


        owned_plates = getattr(user, "plates", [])
        history_plates = [s.plate for s in self._history if getattr(s, "username", None) == user.username]
        
        if plate not in owned_plates and plate not in history_plates:
            raise ReservationError(f"You can only reserve spaces for your registered vehicles. Plate '{plate}' is not linked to your account.")

        if not self._is_returning_customer(user, plate):
            raise ReservationError("Only returning customers with parking history can reserve a space.")

        if self._is_known(plate) or self._find_reserved_position(plate) is not None:
            raise ReservationError(f"Plate {plate} already has a reservation, a parked session, or a waiting-list place.")

        position = self._find_best_space()
        if position is None:
            raise ReservationError("No free parking space is available to reserve.")

        f, s = position
        space = self.grid[f][s]
        space.reserve(plate)
        space.status = "reserved"
        self._push_action("reserve", plate, now, floor=f, slot=s, space_id=space.space_id)
        return {"status": "reserved", "space_id": space.space_id}

    def park_vehicle(self, plate, vehicle_type="car", now=None):
        now = self._now(now)
        plate = normalize_plate(plate)
        vehicle_type = validate_vehicle_type(vehicle_type)

        reserved_pos = self._find_reserved_position(plate)
        if reserved_pos is not None:
            session = self._start_session(plate, vehicle_type, reserved_pos, now)
            f, s = reserved_pos
            self._push_action("park", plate, now, floor=f, slot=s)
            return {
                "status": "parked",
                "plate": plate,
                "floor": f,
                "slot": s,
                "session": session,
            }

        if self._is_known(plate):
            raise DuplicateVehicleError(
                f"Vehicle {plate} is already parked or on the waiting list."
            )

        position = self._find_best_space()
        if position is not None:
            session = self._start_session(plate, vehicle_type, position, now)
            f, s = position
            self._push_action("park", plate, now, floor=f, slot=s)
            return {
                "status": "parked",
                "plate": plate,
                "floor": f,
                "slot": s,
                "session": session,
            }

        if self._waiting.size() >= self.max_waiting:
            raise WaitingListFullError(
                f"The lot and the waiting list are both full "
                f"({self.max_waiting} waiting). {plate} cannot be accepted."
            )
        self._waiting.enqueue(
            {"plate": plate, "vehicle_type": vehicle_type, "queued_at": now}
        )
        self._waiting_plates.add(plate)
        self._push_action("queue", plate, now)
        return {"status": "queued", "plate": plate, "position": self._waiting.size()}

    def exit_vehicle(self, plate, now=None):
        now = self._now(now)
        plate = normalize_plate(plate)

        if not self._active.contains(plate):
            if plate in self._waiting_plates:
                raise VehicleNotFoundError(
                    f"Vehicle {plate} is still on the waiting list, not parked."
                )
            raise VehicleNotFoundError(f"Vehicle {plate} is not in the lot.")

        session = self._active.get(plate)
        session.close(now)
        self.grid[session.floor][session.slot].release()
        self._active.remove(plate)
        self._history.append(session)
        self._push_action(
            "exit", plate, now, floor=session.floor, slot=session.slot, fee=session.fee
        )
        self._mark_customer_history(plate)

        promoted = None
        if not self._waiting.is_empty():
            nxt = self._waiting.dequeue()
            self._waiting_plates.discard(nxt["plate"])
            position = self._find_best_space()
            promoted = self._start_session(
                nxt["plate"], nxt["vehicle_type"], position, now
            )
        return {"closed": session, "fee": session.fee, "promoted": promoted}

    def _mark_customer_history(self, plate):
        for user in self._users.values():
            if isinstance(user, Customer) and getattr(user, "plate", None) == plate:
                user.has_history = True

    def undo_last_action(self):
        if self._actions.is_empty():
            raise NothingToUndoError("There is nothing to undo.")

        action = self._actions.pop()
        kind, plate = action["type"], action["plate"]

        if kind == "exit":
            self._actions.push(action)
            raise UndoNotAllowedError(
                f"The exit of {plate} cannot be undone (fee already calculated)."
            )

        if kind == "park":
            session = self._active.get(plate)
            if session is None:
                self._actions.push(action)
                raise InvalidStateError(f"Cannot undo: {plate} is not parked.")
            self.grid[session.floor][session.slot].release()
            self._active.remove(plate)
            return {"undone": "park", "plate": plate}

        if kind == "queue":
            items = self._drain_queue()
            if not items or items[-1]["plate"] != plate:
                for it in items:
                    self._waiting.enqueue(it)
                self._actions.push(action)
                raise InvalidStateError(
                    f"Cannot undo: {plate} is not last in the queue."
                )
            items.pop()
            for it in items:
                self._waiting.enqueue(it)
            self._waiting_plates.discard(plate)
            return {"undone": "queue", "plate": plate}

        if kind == "reserve":
            f, s = action.get("floor"), action.get("slot")
            try:
                space = self.grid[f][s]
            except (TypeError, IndexError):
                self._actions.push(action)
                raise InvalidStateError(f"Cannot undo reservation for {plate}.")
            if space.reserved_by != plate:
                self._actions.push(action)
                raise InvalidStateError(f"Cannot undo: {plate} does not hold that reservation.")
            space.clear_reservation()
            return {"undone": "reserve", "plate": plate}

        raise InvalidStateError(f"Unknown action type: {kind!r}")

    def is_full(self):
        return self._find_best_space() is None

    def get_session(self, plate):
        return self._active.get(normalize_plate(plate))

    def get_active_sessions(self):
        return list(self._active.values())

    def get_waiting_list(self):
        items = self._drain_queue()
        for it in items:
            self._waiting.enqueue(it)
        return [dict(it) for it in items]

    def get_history(self):
        return list(self._history)

    def load_history(self, sessions):
        self._history.extend(sessions)

    def get_recent_actions(self, n=10):
        items = [self._actions.pop() for _ in range(self._actions.size())]
        for it in reversed(items):
            self._actions.push(it)
        return [dict(it) for it in items[:n]]

    def get_free_spaces(self):
        return [
            (f, s)
            for f, row in enumerate(self.grid)
            for s, sp in enumerate(row)
            if sp.is_free()
        ]

    def get_reserved_spaces(self):
        return [
            sp.to_dict()
            for row in self.grid
            for sp in row
            if sp.status == "reserved"
        ]

    def get_occupancy(self):
        total = self.floors * self.slots_per_floor
        occupied = len(self._active)
        reserved = sum(1 for row in self.grid for sp in row if sp.status == "reserved")
        free = total - occupied - reserved
        return {
            "total": total,
            "occupied": occupied,
            "reserved": reserved,
            "free": free,
            "waiting": self._waiting.size(),
            "occupancy_rate": round(100 * occupied / total, 1) if total else 0.0,
            "by_floor": [sum(1 for sp in row if not sp.is_free()) for row in self.grid],
        }

    
    def snapshot(self):
        reserved = []
        for f, row in enumerate(self.grid):
            for s, sp in enumerate(row):
                if sp.status == "reserved":
                    reserved.append(
                        {
                            "floor": f,
                            "slot": s,
                            "plate": sp.reserved_by,
                            "space_id": sp.space_id,
                        }
                    )
        return {
            "floors": self.floors,
            "slots_per_floor": self.slots_per_floor,
            "max_waiting": self.max_waiting,
            "active": [s.to_dict() for s in self._active.values()],
            "waiting": [
                {
                    "plate": w["plate"],
                    "vehicle_type": w["vehicle_type"],
                    "queued_at": w["queued_at"].isoformat(),
                }
                for w in self.get_waiting_list()
            ],
            "actions": list(reversed(self.get_recent_actions(self._actions.size()))),
            "history": [s.to_dict() for s in self._history],
            "reserved": reserved,
        }

    
    def restore(self, snap):
        try:
            fresh = ParkingLot(
                snap["floors"], snap["slots_per_floor"], snap["max_waiting"]
            )
            for d in snap["active"]:
                if d.get("exit_time") == "":
                    d = dict(d)
                    d["exit_time"] = None
                session = ParkingSession.from_dict(d)
                space = fresh.grid[session.floor][session.slot]
                if not space.is_free() or fresh._active.contains(session.plate):
                    raise InvalidStateError("two vehicles share a space or plate")
                space.occupy(session.plate)
                fresh._active.put(session.plate, session)
            for w in snap["waiting"]:
                if fresh._is_known(w["plate"]):
                    raise InvalidStateError("duplicate plate in snapshot")
                fresh._waiting.enqueue(
                    {
                        "plate": w["plate"],
                        "vehicle_type": w["vehicle_type"],
                        "queued_at": datetime.fromisoformat(w["queued_at"]),
                    }
                )
                fresh._waiting_plates.add(w["plate"])
            if fresh._waiting.size() > fresh.max_waiting:
                raise InvalidStateError("waiting list longer than its limit")
            for a in snap["actions"]:
                fresh._actions.push(dict(a))
            fresh._history = [ParkingSession.from_dict(d) for d in snap["history"]]
            for item in snap.get("reserved") or []:
                f, s = int(item["floor"]), int(item["slot"])
                space = fresh.grid[f][s]
                if not space.is_free():
                    raise InvalidStateError("reserved space is not free")
                space.reserve(item.get("plate"))
        except InvalidStateError:
            raise
        except (KeyError, IndexError, TypeError, ValueError) as err:
            raise InvalidStateError(f"Bad snapshot: {err!r}") from err

        self.floors, self.slots_per_floor = fresh.floors, fresh.slots_per_floor
        self.max_waiting = fresh.max_waiting
        self.grid = fresh.grid
        self._waiting, self._waiting_plates = fresh._waiting, fresh._waiting_plates
        self._active, self._actions = fresh._active, fresh._actions
        self._history = fresh._history
