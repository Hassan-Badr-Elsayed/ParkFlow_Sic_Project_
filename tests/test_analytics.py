from datetime import date

from core.analytics import (
    avg_stay_hours_by_type,
    build_dataframe,
    clean_sessions,
    entries_per_day,
    entries_per_hour,
    get_insights,
    revenue_by_day,
    summary_metrics,
    usage_by_floor,
)

def make_df():
    records = [
        {"session_id": "1", "plate": "ABC123", "vehicle_type": "car", "space_id": "A-01",
         "entry_time": "2026-10-01 08:00:00", "exit_time": "2026-10-01 09:00:00", "duration_min": 60, "fee": 10},
        {"session_id": "2", "plate": "DEF456", "vehicle_type": "car", "space_id": "A-02",
         "entry_time": "2026-10-01 08:30:00", "exit_time": "2026-10-01 10:30:00", "duration_min": 120, "fee": 20},
        {"session_id": "3", "plate": "GHI789", "vehicle_type": "truck", "space_id": "B-01",
         "entry_time": "2026-10-01 14:00:00", "exit_time": "2026-10-01 15:00:00", "duration_min": 60, "fee": 30},
        {"session_id": "4", "plate": "JKL012", "vehicle_type": "motorcycle", "space_id": "A-03",
         "entry_time": "2026-10-02 08:15:00", "exit_time": "2026-10-02 08:45:00", "duration_min": 30, "fee": 5},
        {"session_id": "5", "plate": "MNO345", "vehicle_type": "car", "space_id": "B-02",
         "entry_time": "2026-10-02 17:00:00", "exit_time": "2026-10-02 18:00:00", "duration_min": 60, "fee": 10},
    ]
    df,report= clean_sessions(build_dataframe(records))
    return df

def test_entries_per_hour():
    df = make_df()
    assert entries_per_hour(df)[8] == 3
    assert entries_per_hour(df)[14] == 1


def test_entries_per_day():
    df = make_df()
    assert entries_per_day(df)[date(2026, 10, 1)] == 3

def test_avg_stay_by_type():
    df = make_df()
    result = avg_stay_hours_by_type(df)
    assert result["car"] == 80/60
    assert result["truck"] == 1
    assert result["motorcycle"] == 0.5


def test_usage_by_floor():
    df = make_df()
    result = usage_by_floor(df)
    assert result["A"] == 3
    assert result["B"] == 2


def test_revenue_by_day():
    df = make_df()
    result = revenue_by_day(df)
    assert result[date(2026, 10, 1)] == 60
    assert result[date(2026, 10, 2)] == 15


def test_get_insights():
    df = make_df()
    insights = get_insights(df)
    assert len(insights) >= 2
    assert "08:00" in insights[0]
    assert "Floor A" in insights[1]


def test_clean_sessions_report():
    records = [
        {"session_id": "1", "plate": "ABC123", "vehicle_type": "car", "space_id": "A-01",
         "entry_time": "2026-10-01 08:00:00", "exit_time": "2026-10-01 09:30:00", "duration_min": 90, "fee": 20},
        {"session_id": "2", "plate": "XYZ789", "vehicle_type": "truck", "space_id": "B-02",
         "entry_time": "2026-10-01 08:30:00", "exit_time": None, "duration_min": None, "fee": None},
        {"session_id": "3", "plate": "??", "vehicle_type": "car", "space_id": "A-03",
         "entry_time": "2026-10-01 10:00:00", "exit_time": "2026-10-01 11:00:00", "duration_min": 60, "fee": 10},
        {"session_id": "4", "plate": "DEF456", "vehicle_type": "car", "space_id": "A-04",
         "entry_time": "2026-10-01 12:00:00", "exit_time": "2026-10-01 11:00:00", "duration_min": -60, "fee": 10},
    ]
    df, report = clean_sessions(build_dataframe(records))
    assert len(df) == 1
    assert report == {"rows_in": 4, "rows_dropped": 3}


def test_empty_dataframe_does_not_crash():
    empty, report = clean_sessions(build_dataframe([]))
    assert report == {"rows_in": 0, "rows_dropped": 0}
    assert len(entries_per_hour(empty)) == 0
    assert len(entries_per_day(empty)) == 0
    assert len(avg_stay_hours_by_type(empty)) == 0
    assert len(usage_by_floor(empty)) == 0
    assert len(revenue_by_day(empty)) == 0
    assert get_insights(empty) == ["No data available"]

def test_revenue_ignores_missing_and_negative_fees():
    records = [
        {
            "session_id": "1",
            "plate": "ABC123",
            "vehicle_type": "car",
            "space_id": "A-01",
            "entry_time": "2026-10-01 08:00:00",
            "exit_time": "2026-10-01 09:00:00",
            "duration_min": 60,
            "fee": 20,
        },
        {
            "session_id": "2",
            "plate": "DEF456",
            "vehicle_type": "car",
            "space_id": "A-02",
            "entry_time": "2026-10-01 09:00:00",
            "exit_time": "2026-10-01 10:00:00",
            "duration_min": 60,
            "fee": None,
        },
        {
            "session_id": "3",
            "plate": "GHI789",
            "vehicle_type": "car",
            "space_id": "A-03",
            "entry_time": "2026-10-01 10:00:00",
            "exit_time": "2026-10-01 11:00:00",
            "duration_min": 60,
            "fee": -10,
        },
    ]

    df, report = clean_sessions(build_dataframe(records))

    assert len(df) == 3

    revenue = revenue_by_day(df)

    assert revenue[date(2026, 10, 1)] == 20

def test_insights_include_highest_revenue_day():
    df = make_df()

    insights = get_insights(df)
    revenue = revenue_by_day(df)
    best_day = revenue.idxmax()
    best_revenue = revenue.max()

    expected = (
        f"Highest revenue day is {best_day} "
        f"with revenue {best_revenue:.2f}"
    )

    assert expected in insights

def test_missing_duration_is_computed():
    records = [{"session_id": "1", "plate": "abc123", "vehicle_type": "car",
                "space_id": "A-01", "entry_time": "2026-10-01 08:00:00",
                "exit_time": "2026-10-01 09:00:00", "duration_min": None, "fee": 10}]
    df, _ = clean_sessions(build_dataframe(records))
    assert df["duration_min"].iloc[0] == 60
    assert df["plate"].iloc[0] == "ABC123"

def test_summary_metrics():
    m = summary_metrics(make_df())
    assert m["total_sessions"]==5
    assert m["total_revenue"]==75
    assert m["avg_stay_hours"]==1.1

def test_summary_metrics_empty():
    empty, _ = clean_sessions(build_dataframe([]))
    assert summary_metrics(empty)=={
        "total_sessions": 0.0,
        "total_revenue": 0.0,
        "avg_stay_hours" :0.0,
    }

