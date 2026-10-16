import streamlit as st

from core.exceptions import ParkFlowError
from ui.state import get_lot, save_all

def _session_rows(sessions):
    rows = []
    for session in sessions:
        data = session.to_dict() if hasattr(session, "to_dict") else dict(session)
        rows.append(data)
    return rows

def render_operations_tab():
    lot = get_lot()
    st.subheader("⚙️ Gate Operations")
    st.caption("Walk-in registration, reserved check-in, exits, and undo.")
    
    st.divider() 


    st.markdown("### 🟢 Park / Check in")
    plate = st.text_input("License plate", key="ops_plate", help="Enter the vehicle's plate number")
    vehicle_type = st.selectbox(
        "Vehicle type",
        ["car", "motorcycle", "truck"],
        key="ops_vtype",
    )
    if st.button("Park vehicle", key="ops_park"):
        try:
            result = lot.park_vehicle(plate, vehicle_type)
            save_all()
            if result["status"] == "parked":
                st.success(
                    f"✅ {result['plate']} parked at floor {result['floor']}, "
                    f"slot {result['slot']}."
                )
            elif result["status"] == "queued":
                st.warning(
                    f"⏳ {result['plate']} joined the waiting list "
                    f"(position {result['position']})."
                )
            else:
                st.info(str(result))
        except ParkFlowError as err:
            st.error(str(err))

    st.divider() 


    
    st.markdown("### 🔴 Exit")
    exit_plate = st.text_input("Exiting plate", key="ops_exit_plate", help="Enter the plate number leaving the lot")
    if st.button("Exit vehicle", key="ops_exit"):
        try:
            result = lot.exit_vehicle(exit_plate)
            save_all()
            msg = f"✅ {result['closed'].plate} exited. Fee: {result['fee']:.2f}"
            if result.get("promoted") is not None:
                promoted = result["promoted"]
                msg += (
                    f" | Promoted {promoted.plate} to floor {promoted.floor}, "
                    f"slot {promoted.slot}."
                )
            st.success(msg)
        except ParkFlowError as err:
            st.error(str(err))

    st.divider() 


    
    st.markdown("### ↩️ Undo Last Action")
    st.caption("Revert the last check-in or queue assignment.")
    if st.button("Undo last action", key="ops_undo"):
        try:
            result = lot.undo_last_action()
            save_all()
            st.success(
                f"✅ Undid {result.get('undone')} for {result.get('plate')}."
            )
        except ParkFlowError as err:
            st.error(str(err))

    st.divider() 



    st.markdown("### 📋 Waiting list")
    waiting = lot.get_waiting_list()
    waiting_rows = []
    for item in waiting:
        queued = item.get("queued_at")
        waiting_rows.append(
            {
                "plate": item.get("plate"),
                "vehicle_type": item.get("vehicle_type"),
                "queued_at": queued.isoformat() if hasattr(queued, "isoformat") else queued,
            }
        )
    if waiting_rows:
        st.dataframe(waiting_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Waiting list is empty.")

    st.divider() 
    st.markdown("### 🅿️ Active sessions")
    active = _session_rows(lot.get_active_sessions())
    if active:
        st.dataframe(active, use_container_width=True, hide_index=True)
    else:
        st.info("No vehicles are parked.")

    st.divider() 

    st.markdown("### 🕒 Recent actions")
    recent = lot.get_recent_actions(15)
    if recent:
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No actions yet.")