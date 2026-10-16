from datetime import datetime, timedelta

import pytest

from core.config import FLOORS, SLOTS_PER_FLOOR, MAX_WAITING
from core.exceptions import ParkFlowError, WaitingListFullError
from core.parking_service import ParkingLot

T0 = datetime(2026, 3, 1, 9, 0)
CAPACITY = FLOORS * SLOTS_PER_FLOOR


def test_full_day_scenario():
    lot = ParkingLot()
    # 1. Fill the lot
    for i in range(CAPACITY):
        r = lot.park_vehicle(f"CAR{i:03d}", "car", now=T0)
        assert r["status"] == "parked"
    assert lot.is_full() and lot.get_occupancy()["occupancy_rate"] == 100.0

    # 2. Fill the waiting list, then overflow
    for i in range(MAX_WAITING):
        assert lot.park_vehicle(f"WAIT{i:02d}", "car", now=T0)["status"] == "queued"
    with pytest.raises(WaitingListFullError):
        lot.park_vehicle("LATE01", "car", now=T0)

    # 3. Undo the last queue-join, then the overflow vehicle can queue
    assert lot.undo_last_action()["undone"] == "queue"
    assert lot.park_vehicle("LATE01", "car", now=T0)["position"] == MAX_WAITING

    # 4. Cars leave: waiting vehicles enter in FIFO order, fees are charged
    promoted_order = []
    for i in range(MAX_WAITING):
        r = lot.exit_vehicle(f"CAR{i:03d}", now=T0 + timedelta(hours=2, minutes=i))
        assert r["fee"] > 0
        promoted_order.append(r["promoted"].plate)
    assert promoted_order == [f"WAIT{i:02d}" for i in range(MAX_WAITING - 1)] + ["LATE01"]
    assert lot.get_waiting_list() == []
    assert lot.get_occupancy()["occupied"] == CAPACITY
    assert len(lot.get_history()) == MAX_WAITING

    # 5. Lot drains completely
    for s in lot.get_active_sessions():
        lot.exit_vehicle(s.plate, now=T0 + timedelta(hours=5))
    assert lot.get_occupancy()["occupied"] == 0
    assert len(lot.get_history()) == CAPACITY + MAX_WAITING


def test_snapshot_mid_scenario_then_continue():
    lot = ParkingLot()
    for i in range(CAPACITY + 3):
        lot.park_vehicle(f"CAR{i:03d}", "car", now=T0)
    snap = lot.snapshot()
    restored = ParkingLot()
    restored.restore(snap)
    r1 = lot.exit_vehicle("CAR005", now=T0 + timedelta(hours=1))
    r2 = restored.exit_vehicle("CAR005", now=T0 + timedelta(hours=1))
    assert r1["promoted"].plate == r2["promoted"].plate == f"CAR{CAPACITY:03d}"
    assert lot.snapshot() == restored.snapshot()


def test_invalid_use_never_crashes_with_a_non_parkflow_error():
    """Every bad input must raise a ParkFlowError (the UI catches only that)."""
    lot = ParkingLot()
    bad_calls = [
        lambda: lot.park_vehicle("", "car"),
        lambda: lot.park_vehicle("A", "car"),
        lambda: lot.park_vehicle("ABC123", ""),
        lambda: lot.park_vehicle(None, "car"),
        lambda: lot.exit_vehicle("NOPE99"),
        lambda: lot.exit_vehicle("%%%"),
        lambda: lot.undo_last_action(),
        lambda: lot.get_session("%%%"),
    ]
    for call in bad_calls:
        with pytest.raises(ParkFlowError):
            call()
    assert lot.get_occupancy()["occupied"] == 0


def test_fee_grows_with_time():
    lot = ParkingLot()
    lot.park_vehicle("AAA111", "car", now=T0)
    lot.park_vehicle("BBB222", "car", now=T0)
    short = lot.exit_vehicle("AAA111", now=T0 + timedelta(minutes=1))["fee"]
    long_ = lot.exit_vehicle("BBB222", now=T0 + timedelta(hours=3))["fee"]
    assert long_ > short > 0
