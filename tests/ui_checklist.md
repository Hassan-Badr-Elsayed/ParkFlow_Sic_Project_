# ParkFlow UI manual test checklist

Run from the project root:

```bash
streamlit run app.py
```

Demo passwords match the username unless an admin created a custom employee password.

| Account | Role | Username / password | Notes |
|---|---|---|---|
| Admin | admin | `admin_boss` / `admin_boss` | Dashboard, history, operations |
| Gate operator | employee | `emp_john` / `emp_john` | Operations, history |
| Returning customer | customer | `cust_sarah` / `cust_sarah` | `has_history=True`, can reserve |
| New customer | customer | `cust_alex` / `cust_alex` | `has_history=False`, reserve must fail |
| Returning customer | customer | `cust_mona` / `cust_mona` | `has_history=True` |

Missing or empty CSVs in `data/` must still boot the app (empty lot, no crash).

## Auth and sidebar

- [ ] Unauthenticated visit shows the login form only (no lot tabs).
- [ ] Wrong username shows `AuthenticationError` via `st.error` (not a traceback).
- [ ] Wrong password shows `AuthenticationError` via `st.error`.
- [ ] Valid admin / employee / customer login sets `current_user` and routes the correct tabs.
- [ ] Sidebar shows username, role, occupied/free/reserved/waiting, occupancy rate, and a Log out button.
- [ ] Log out clears the session user and returns to the login form.
- [ ] Sidebar metrics update after park / exit / reserve (live occupancy).

## Employee operations (`ui/operations_tab.py`)

- [ ] Park a walk-in plate (`ABC123`, car) → status parked at the closest free space (floor 0, slot 0 when empty).
- [ ] Park the same plate again → `ParkFlowError` / duplicate error in `st.error`; CSVs unchanged for that failure.
- [ ] Invalid plate (`!!`) and invalid type are rejected with `st.error`.
- [ ] Fill the lot, then park another vehicle → queued; waiting-list table shows FIFO order.
- [ ] Overflow past `MAX_WAITING` → waiting-list full error.
- [ ] Exit a parked plate → fee shown; space freed; if the queue is non-empty the first waiter is promoted.
- [ ] Exit an unknown plate → error, no crash.
- [ ] Undo last park → space and plate become free again; history does not gain a session.
- [ ] Undo last queue-join → plate leaves the waiting list.
- [ ] Undo after an exit → undo-not-allowed error; history stays.
- [ ] Reserved check-in: as a returning customer, reserve a plate, then as employee park that **same plate** → occupies the reserved space (not a new greedy space); reservation is cleared.
- [ ] After every successful mutation, `data/parked.csv`, `data/waiting.csv`, `data/sessions.csv`, and/or `data/users.csv` update immediately (`save_all()`).

## Customer driver view (`ui/driver_tab.py`)

- [ ] Free-space table lists only `is_free()` cells (excludes occupied and reserved).
- [ ] `cust_sarah` reserves `SAR123` → success, `status=reserved`, `space_id` shown; grid/sidebar reserved count increments.
- [ ] Same plate reserved again → `ReservationError`.
- [ ] `cust_alex` (no history) reserve → `ReservationError` about returning customers.
- [ ] Employee/admin cannot use this tab as a customer; customers do not see employee create/delete.
- [ ] Sequential search on an active/history/reserved plate reports matches and comparison count (full scan).
- [ ] Binary search runs on a **copy sorted by `plate` with `merge_sort` first**, then `binary_search`; shows index, search comparisons, sort comparisons, and recursive calls.
- [ ] Unsorted original list is not mutated (search another plate; order of source tables still makes sense).

## History (`ui/history_tab.py`)

- [ ] Empty history shows a friendly empty state.
- [ ] After some exits, table lists closed sessions.
- [ ] `insertion_sort` by `fee` ascending/descending shows table plus `comparisons` and `shifts`.
- [ ] `merge_sort` by `entry_time` shows table plus `comparisons` and `recursive_calls`.
- [ ] `compare_sorts` shows both metric blocks and `same_result`.

## Admin dashboard (`ui/dashboard_tab.py`)

- [ ] 2D grid table: one row per floor, slot columns, cell values `free` / `occupied` / `reserved`.
- [ ] Cleaning report: `rows_in` and `rows_dropped` reflect dirty rows in `data/sessions.csv` (empty exit, invalid plate, negative duration).
- [ ] Date range and vehicle-type filters shrink summary metrics and charts.
- [ ] Summary metrics: total sessions, revenue, average stay hours (empty filter set does not crash).
- [ ] `get_insights` bullets render (peak hour, busiest floor, top type, highest revenue day) or “No data available”.
- [ ] Three charts render: entries/hour (`st.bar_chart`), entries/day (`st.line_chart`), usage/floor (`st.bar_chart`). Empty data shows a caption instead of an exception.
- [ ] Analytics functions receive only plain lists of dicts / DataFrames (no `ParkingSession` objects).
- [ ] Create employee `gate_ann` with a password → appears in the users table; login works with that password.
- [ ] Duplicate username → `DuplicateUserError` in `st.error`.
- [ ] Delete that employee → gone from table and `data/users.csv`; that login no longer works.
- [ ] Delete is limited to `employee` role (admins/customers are not in the delete dropdown).

## Persistence and restart

- [ ] Park two cars, queue one, reserve one (as returning customer), create an employee, stop Streamlit, start again: parked, waiting, history, users, and occupancy match the CSVs.
- [ ] Missing `data/parked.csv` / `data/waiting.csv` still starts (treated as empty).
- [ ] `users.csv` without a `password` column still authenticates with password = username.

## Role routing (`app.py`)

- [ ] Admin: Dashboard, History, Operations.
- [ ] Employee: Operations, History (no employee-create required, no customer reserve tab).
- [ ] Customer: Driver, History (no employee management).
