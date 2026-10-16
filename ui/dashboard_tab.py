import streamlit as st

from core.analytics import (
    build_dataframe,
    clean_sessions,
    entries_per_day,
    entries_per_hour,
    get_insights,
    summary_metrics,
    usage_by_floor,
)
from core.exceptions import ParkFlowError
from ui.state import analytics_records, get_lot, save_all


def render_colored_metrics(occ):
    st.markdown("""
        <style>
        .metric-box {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #ddd;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .metric-green { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
        .metric-red { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
        .metric-yellow { background-color: #fff3cd; color: #856404; border-color: #ffeeba; }
        .metric-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 5px; }
        .metric-value { font-size: 2rem; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="metric-box metric-green">
                <div class="metric-title">🟢 متاحة<br>Available</div>
                <div class="metric-value">{occ['free']}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-box metric-red">
                <div class="metric-title">🔴 مشغولة<br>Occupied</div>
                <div class="metric-value">{occ['occupied']}</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="metric-box metric-yellow">
                <div class="metric-title">⏳ في الانتظار<br>Queue</div>
                <div class="metric-value">{occ['waiting']}</div>
            </div>
        """, unsafe_allow_html=True)

def render_colored_grid(lot):
    st.markdown("### 🗺️ خريطة المواقف | Parking Floor Map")
    
    slots_count = len(lot.grid[0]) if lot.grid else 10
    
    html = f"<div style='display: grid; grid-template-columns: repeat({slots_count}, 1fr); gap: 10px; margin-bottom: 30px;'>"
    
    for floor in lot.grid:
        for space in floor:
            space_name = f"{chr(65 + space.floor)}{space.slot}"
            
            plate_num = getattr(space, "plate", "")
            if not plate_num and hasattr(space, "to_dict"):
                plate_num = space.to_dict().get("plate", "")
            if not plate_num:
                plate_num = "" 
            
            if space.is_free():
                bg_color = "#28a745"
                text = f"<b>{space_name}</b><br><span style='font-size: 0.8rem;'>Free</span>"
            elif space.status == "reserved":
                bg_color = "#ffc107"
                text = f"<b>{space_name}</b><br><span style='font-size: 0.8rem;'>Reserved</span><br><span style='font-size: 0.7rem; color: #333;'>{plate_num}</span>"
            else:
                bg_color = "#dc3545"
                text = f"<b>{space_name}</b><br><span style='font-size: 0.8rem;'>busy</span><br><span style='font-size: 0.7rem;'>{plate_num}</span>"
                
            html += f"<div style='background-color: {bg_color}; color: white; padding: 15px 5px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{text}</div>"
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def _prepare_analytics_df():
    records = analytics_records()
    df = build_dataframe(records)
    cleaned, report = clean_sessions(df)
    return records, cleaned, report


def render_dashboard_tab():
    lot = get_lot()
    st.subheader("📊 Admin Dashboard")


    occ = lot.get_occupancy()
    render_colored_metrics(occ)
    
    st.divider()


    render_colored_grid(lot)

    st.divider()
    

    st.markdown("### 📈 Data Analytics")
    
    records, cleaned, report = _prepare_analytics_df()
    
    st.markdown("**Data cleaning report**")
    st.json(report)
    st.caption(f"Raw rows passed to analytics: {len(records)}")

    if cleaned.empty:
        filtered = cleaned
        vehicle_types = []
    else:
        min_day = cleaned["entry_time"].min().date()
        max_day = cleaned["entry_time"].max().date()
        vehicle_types = sorted(
            str(v) for v in cleaned["vehicle_type"].dropna().unique().tolist()
        )
        c1, c2 = st.columns(2)
        with c1:
            date_range = st.date_input(
                "Date range",
                value=(min_day, max_day),
                min_value=min_day,
                max_value=max_day,
            )
        with c2:
            selected_types = st.multiselect(
                "Vehicle type",
                options=vehicle_types,
                default=vehicle_types,
            )
        filtered = cleaned
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            filtered = filtered[
                (filtered["entry_time"].dt.date >= start)
                & (filtered["entry_time"].dt.date <= end)
            ]
        if selected_types:
            filtered = filtered[filtered["vehicle_type"].isin(selected_types)]
        elif vehicle_types:
            filtered = filtered.iloc[0:0]

    st.markdown("**Summary metrics**")
    metrics = summary_metrics(filtered)
    s1, s2, s3 = st.columns(3)
    s1.metric("Total sessions", metrics.get("total_sessions", 0))
    s2.metric("Total revenue", f"{float(metrics.get('total_revenue', 0.0)):.2f}")
    s3.metric("Avg stay (hours)", f"{float(metrics.get('avg_stay_hours', 0.0)):.2f}")

    st.markdown("**Insights**")
    for line in get_insights(filtered):
        st.write(f"- {line}")

    st.markdown("**Charts**")
    hour_counts = entries_per_hour(filtered)
    day_counts = entries_per_day(filtered)
    floor_counts = usage_by_floor(filtered)

    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.caption("Entries / hour")
        if hour_counts is None or getattr(hour_counts, "empty", True):
            st.write("No hourly data.")
        else:
            st.bar_chart(hour_counts)
    with ch2:
        st.caption("Entries / day")
        if day_counts is None or getattr(day_counts, "empty", True):
            st.write("No daily data.")
        else:
            st.line_chart(day_counts)
    with ch3:
        st.caption("Usage / floor")
        if floor_counts is None or getattr(floor_counts, "empty", True):
            st.write("No floor data.")
        else:
            st.bar_chart(floor_counts)

    st.divider()
    
    st.markdown("### 👥 Employee account management")
    st.caption("Create or delete Gate Operator (Employee) accounts. Saved to users.csv immediately.")
    from ui.state import get_user_manager
    um = get_user_manager()
    
    users = um.get_users()
    user_rows = [
        {
            "User ID": u.user_id,
            "Username": u.username,
            "Role": u.role,
            "Email": getattr(u, "email", ""),
            "Phone": getattr(u, "phone", ""),
            "Has History": getattr(u, "has_history", False),
        }
        for u in users
    ]
    if user_rows:
        st.dataframe(user_rows, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("Create employee")
        new_username = st.text_input("New username", key="emp_new_user")
        new_email = st.text_input("Email", key="emp_new_email")
        new_password = st.text_input("Password", type="password", key="emp_new_pw")
        if st.button("Create employee", key="emp_create"):
            try:
                emp = um.create_employee(new_username, email=new_email, password=new_password) # التعديل هنا
                save_all()
                st.success(f"Created employee `{emp.username}` (id {emp.user_id}).")
            except ParkFlowError as err:
                st.error(str(err))

    with right:
        st.markdown("Delete employee")
        employees = [u.username for u in users if str(getattr(u, "role", "")).lower() == "employee"]
        if not employees:
            st.caption("No employee accounts.")
        else:
            target = st.selectbox("Employee to delete", employees, key="emp_del_sel")
            if st.button("Delete employee", key="emp_delete"):
                try:
                    um.delete_employee(target) 
                    save_all()
                    st.success(f"Deleted employee `{target}`.")
                except ParkFlowError as err:
                    st.error(str(err))