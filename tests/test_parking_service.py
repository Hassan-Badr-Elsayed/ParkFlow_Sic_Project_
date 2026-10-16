import json
from datetime import datetime, timedelta

import pytest

from core.exceptions import (
    DuplicateVehicleError, InvalidPlateError, InvalidStateError,
    InvalidVehicleTypeError, NothingToUndoError, UndoNotAllowedError,
    VehicleNotFoundError, WaitingListFullError,
)
from core.models import Admin, Customer, Employee
from core.parking_service import ParkingLot

T0 = datetime(2026, 1, 1, 8, 0)


@pytest.fixture
def lot():
    return ParkingLot(floors=2, slots_per_floor=3, max_waiting=2)


def fill(lot, n, prefix="CAR"):
    for i in range(n):
        lot.park_vehicle(f"{prefix}{i:03d}", "car", now=T0)


# ---------- parking + greedy allocation ----------
def test_first_vehicle_gets_closest_space(lot):
    r = lot.park_vehicle("abc 123", "car", now=T0)
    assert (r["status"], r["floor"], r["slot"], r["plate"]) == ("parked", 0, 0, "ABC123")


def test_spaces_fill_in_distance_order(lot):
    spots = [lot.park_vehicle(f"CAR{i}", "car", now=T0) for i in range(6)]
    assert [(s["floor"], s["slot"]) for s in spots] == \
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]


def test_greedy_reuses_closest_freed_space(lot):
    fill(lot, 4)                                   # floor 0 full, (1,0) used
    lot.exit_vehicle("CAR001", now=T0 + timedelta(hours=1))   # frees (0,1)
    r = lot.park_vehicle("NEW001", "car", now=T0)
    assert (r["floor"], r["slot"]) == (0, 1)       # not (1,1)


def test_invalid_plate_and_type_rejected(lot):
    with pytest.raises(InvalidPlateError):
        lot.park_vehicle("!!", "car")
    with pytest.raises(InvalidVehicleTypeError):
        lot.park_vehicle("ABC123", "boat")
    assert lot.get_occupancy()["occupied"] == 0    # nothing half-saved


def test_duplicate_when_parked(lot):
    lot.park_vehicle("ABC123", "car", now=T0)
    with pytest.raises(DuplicateVehicleError):
        lot.park_vehicle("abc-123", "truck", now=T0)    # same plate after normalizing


def test_duplicate_when_waiting(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    with pytest.raises(DuplicateVehicleError):
        lot.park_vehicle("WAIT01", "car", now=T0)


# ---------- waiting list ----------
def test_full_lot_queues_vehicle(lot):
    fill(lot, 6)
    r = lot.park_vehicle("WAIT01", "car", now=T0)
    assert r == {"status": "queued", "plate": "WAIT01", "position": 1}
    assert lot.is_full()


def test_waiting_list_full_raises(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    lot.park_vehicle("WAIT02", "car", now=T0)
    with pytest.raises(WaitingListFullError):
        lot.park_vehicle("WAIT03", "car", now=T0)
    assert len(lot.get_waiting_list()) == 2


def test_get_waiting_list_keeps_order_and_does_not_consume(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    lot.park_vehicle("WAIT02", "truck", now=T0)
    first = [w["plate"] for w in lot.get_waiting_list()]
    second = [w["plate"] for w in lot.get_waiting_list()]
    assert first == second == ["WAIT01", "WAIT02"]


# ---------- exit ----------
def test_exit_closes_session_and_frees_space(lot):
    lot.park_vehicle("ABC123", "car", now=T0)
    r = lot.exit_vehicle("abc123", now=T0 + timedelta(minutes=90))
    assert r["fee"] > 0 and r["promoted"] is None
    assert lot.get_occupancy()["occupied"] == 0
    assert [s.plate for s in lot.get_history()] == ["ABC123"]
    assert lot.get_session("ABC123") is None


def test_exit_unknown_vehicle(lot):
    with pytest.raises(VehicleNotFoundError):
        lot.exit_vehicle("ZZZ999")


def test_exit_of_waiting_vehicle_is_refused(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    with pytest.raises(VehicleNotFoundError):
        lot.exit_vehicle("WAIT01")


def test_exit_twice_second_fails(lot):
    lot.park_vehicle("ABC123", "car", now=T0)
    lot.exit_vehicle("ABC123", now=T0 + timedelta(hours=1))
    with pytest.raises(VehicleNotFoundError):
        lot.exit_vehicle("ABC123")


def test_exit_promotes_first_waiting_into_freed_space(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    lot.park_vehicle("WAIT02", "car", now=T0)
    r = lot.exit_vehicle("CAR002", now=T0 + timedelta(hours=2))   # frees (0,2)
    assert r["promoted"].plate == "WAIT01"
    assert (r["promoted"].floor, r["promoted"].slot) == (0, 2)
    assert [w["plate"] for w in lot.get_waiting_list()] == ["WAIT02"]
    assert lot.get_session("WAIT01") is not None


# ---------- undo ----------
def test_undo_park_frees_space_and_skips_history(lot):
    lot.park_vehicle("ABC123", "car", now=T0)
    assert lot.undo_last_action() == {"undone": "park", "plate": "ABC123"}
    assert lot.get_occupancy()["occupied"] == 0
    assert lot.get_history() == []
    lot.park_vehicle("ABC123", "car", now=T0)       # plate usable again


def test_undo_queue_join_removes_last_waiting(lot):
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "car", now=T0)
    lot.park_vehicle("WAIT02", "car", now=T0)
    assert lot.undo_last_action()["undone"] == "queue"
    assert [w["plate"] for w in lot.get_waiting_list()] == ["WAIT01"]
    lot.park_vehicle("WAIT02", "car", now=T0)       # allowed again


def test_undo_goes_back_step_by_step(lot):
    lot.park_vehicle("AAA111", "car", now=T0)
    lot.park_vehicle("BBB222", "car", now=T0)
    lot.undo_last_action()
    assert lot.get_session("BBB222") is None and lot.get_session("AAA111")
    lot.undo_last_action()
    assert lot.get_active_sessions() == []


def test_undo_exit_not_allowed_and_blocks_older_undo(lot):
    lot.park_vehicle("ABC123", "car", now=T0)
    lot.exit_vehicle("ABC123", now=T0 + timedelta(hours=1))
    with pytest.raises(UndoNotAllowedError):
        lot.undo_last_action()
    assert len(lot.get_history()) == 1              # nothing was changed
    assert lot.get_recent_actions(1)[0]["type"] == "exit"   # marker still on top


def test_undo_with_nothing(lot):
    with pytest.raises(NothingToUndoError):
        lot.undo_last_action()


# ---------- getters ----------
def test_occupancy_numbers(lot):
    fill(lot, 4)
    o = lot.get_occupancy()
    assert (o["total"], o["occupied"], o["free"], o["waiting"]) == (6, 4, 2, 0)
    assert o["by_floor"] == [3, 1] and o["occupancy_rate"] == 66.7


def test_free_spaces_list(lot):
    fill(lot, 5)
    assert lot.get_free_spaces() == [(1, 2)]


def test_recent_actions_newest_first_and_stack_untouched(lot):
    lot.park_vehicle("AAA111", "car", now=T0)
    lot.park_vehicle("BBB222", "car", now=T0)
    recent = lot.get_recent_actions()
    assert [a["plate"] for a in recent] == ["BBB222", "AAA111"]
    assert lot.get_recent_actions(1)[0]["plate"] == "BBB222"
    lot.undo_last_action()                           # stack still works
    assert lot.get_session("BBB222") is None


def test_load_history(lot):
    lot.park_vehicle("AAA111", "car", now=T0)
    s = lot.exit_vehicle("AAA111", now=T0 + timedelta(hours=1))["closed"]
    other = ParkingLot(floors=2, slots_per_floor=3)
    other.load_history([s])
    assert other.get_history()[0].plate == "AAA111"


# ---------- snapshot / restore ----------
def build_busy_lot():
    lot = ParkingLot(floors=2, slots_per_floor=3, max_waiting=2)
    fill(lot, 6)
    lot.park_vehicle("WAIT01", "truck", now=T0)
    lot.park_vehicle("WAIT02", "car", now=T0)
    lot.exit_vehicle("CAR000", now=T0 + timedelta(hours=1))     # promotes WAIT01
    return lot


def test_snapshot_restore_round_trip():
    lot = build_busy_lot()
    snap = json.loads(json.dumps(lot.snapshot()))   # must be JSON-safe
    new = ParkingLot()                              # different size on purpose
    new.restore(snap)
    assert new.snapshot() == lot.snapshot()
    assert [w["plate"] for w in new.get_waiting_list()] == ["WAIT02"]
    assert new.get_occupancy() == lot.get_occupancy()


def test_restored_lot_keeps_working():
    new = ParkingLot()
    new.restore(build_busy_lot().snapshot())
    r = new.exit_vehicle("CAR001", now=T0 + timedelta(hours=3))
    assert r["promoted"].plate == "WAIT02"
    with pytest.raises(UndoNotAllowedError):        # action stack survived too
        new.undo_last_action()
    with pytest.raises(DuplicateVehicleError):
        new.park_vehicle("CAR002", "car", now=T0)   # active table survived


def test_restore_is_independent_copy():
    lot = build_busy_lot()
    snap = lot.snapshot()
    new = ParkingLot()
    new.restore(snap)
    new.exit_vehicle("CAR002", now=T0 + timedelta(hours=2))
    assert lot.get_session("CAR002") is not None    # original untouched


def test_bad_snapshot_leaves_lot_unchanged(lot):
    lot.park_vehicle("AAA111", "car", now=T0)
    before = lot.snapshot()
    with pytest.raises(InvalidStateError):
        lot.restore({"floors": 2})
    bad = build_busy_lot().snapshot()
    bad["active"].append(dict(bad["active"][0]))    # same plate twice
    with pytest.raises(InvalidStateError):
        lot.restore(bad)
    assert lot.snapshot() == before


def test_empty_lot_snapshot_restore():
    a = ParkingLot()
    b = ParkingLot()
    b.restore(a.snapshot())
    assert b.get_occupancy()["occupied"] == 0 and b.get_waiting_list() == []


# ---------- users table ----------
@pytest.fixture
def users_lot(lot):
    lot.load_users([Admin("admin", "root"), Employee("sara", "pw1"), Customer("omar", "pw2")])
    return lot


def test_get_user_returns_user_or_none(users_lot):
    assert users_lot.get_user("omar").role == "customer"
    assert users_lot.get_user("ghost") is None


def test_username_lookup_ignores_case_and_spaces(users_lot):
    assert users_lot.get_user("  SARA ").username == "sara"


def test_load_users_rejects_duplicate_usernames(lot):
    with pytest.raises(InvalidStateError):
        lot.load_users([Employee("sara", "a"), Customer("SARA", "b")])


def test_load_users_replaces_old_accounts(users_lot):
    users_lot.load_users([Customer("nour", "x")])
    assert users_lot.get_user("sara") is None and users_lot.get_user("nour")


def test_restore_does_not_touch_users(users_lot):
    snap = users_lot.snapshot()
    users_lot.restore(snap)
    assert users_lot.get_user("sara") is not None
    assert "users" not in snap
