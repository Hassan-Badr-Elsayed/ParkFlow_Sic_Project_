import streamlit as st

from core.exceptions import InvalidPlateError, ParkFlowError, ReservationError
from core.searching import binary_search, sequential_search
from core.sorting import merge_sort
from core.validators import normalize_plate
from ui.state import get_current_user, get_lot, save_all

def _lookup_records(lot):
    records = []
    for session in lot.get_active_sessions():
        data = session.to_dict()
        data["state"] = "active"
        records.append(data)
    for session in lot.get_history():
        data = session.to_dict()
        data["state"] = "history"
        records.append(data)
    for item in lot.get_reserved_spaces():
        records.append(
            {
                "plate": item.get("reserved_by"),
                "space_id": item.get("space_id"),
                "floor": item.get("floor"),
                "slot": item.get("slot"),
                "state": "reserved",
            }
        )
    return records

def render_driver_tab():
    lot = get_lot()
    user = get_current_user()

    st.subheader("🚗 Customer Portal")
    occ = lot.get_occupancy()
    
    st.write(f"🟢 Free spaces: **{occ['free']}** &nbsp; | &nbsp; 🟡 Reserved: **{occ.get('reserved', 0)}**")

    st.markdown("### 🗺️ Available Spaces Map")
    st.caption("Green means available, Red means occupied, Yellow means reserved.")
    
    slots_count = len(lot.grid[0]) if lot.grid else 10
    html = f"<div style='display: grid; grid-template-columns: repeat({slots_count}, 1fr); gap: 10px; margin-bottom: 20px;'>"
    
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
                text = f"<b>{space_name}</b><br><span style='font-size: 0.8rem;'>Reserved</span>"
            else:
                bg_color = "#dc3545" 
                text = f"<b>{space_name}</b><br><span style='font-size: 0.8rem;'>busy</span>"
                
            html += f"<div style='background-color: {bg_color}; color: white; padding: 12px 2px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-size: 0.85rem;'>{text}</div>"
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    if str(getattr(user, "role", "")).lower() == "admin":
        st.info("💡 You are in View-Only mode. Vehicle management and reservations are restricted to Customers.")
        return
###########################################################################
    st.markdown("### 🚘 My Vehicles")
    
    owned_plates = getattr(user, "plates", [])
    if owned_plates:
        st.write("Registered plates: " + ", ".join([f"`{p}`" for p in owned_plates]))
    else:
        st.caption("No vehicles registered yet.")
        
    with st.expander("➕ Add a new vehicle to your account"):
        with st.form("add_vehicle_form", clear_on_submit=True):
            new_plate = st.text_input("New License Plate")
            submit_vehicle = st.form_submit_button("Add Vehicle")
            
        if submit_vehicle:
            if not new_plate:
                st.error("Please enter a license plate.")
            else:
                try:
                    from ui.state import get_user_manager
                    um = get_user_manager()
                    um.add_vehicle_to_customer(user.username, new_plate)
                    save_all()
                    st.success(f"Plate {new_plate.upper()} added successfully!")
                    
                    import time
                    time.sleep(1)
                    st.rerun()
                except ParkFlowError as err:
                    st.error(str(err))
    st.divider()

    st.markdown("### 📌 Reserve a space")
    st.caption("Advance booking for returning customers. Closest space allocated greedily.")
    
    with st.form("reserve_form", clear_on_submit=False):
        plate = st.text_input("Your license plate")
        submit_reserve = st.form_submit_button("Reserve Space")
        
    if submit_reserve:
        if not plate:
            st.error("Please enter a license plate.")
        else:
            try:
                result = lot.reserve_space(plate, user)
                save_all()
                st.success(f"Successfully reserved space **{result['space_id']}** for plate {plate.upper()}.")

                import time
                time.sleep(1)
                st.rerun()

            except ReservationError as err:
                st.error(str(err))
            except ParkFlowError as err:
                st.error(str(err))

    reserved = lot.get_reserved_spaces()
    if reserved:
        st.markdown("**Your Current Reservations:**")
        st.dataframe(reserved, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 🔍 Plate Lookup")
    
    with st.form("search_form", clear_on_submit=False):
        target = st.text_input("Enter plate to search")
        submit_search = st.form_submit_button("Search Vehicle")
        
    if submit_search:
        if not target:
            st.warning("Please enter a plate to search.")
        else:
            records = _lookup_records(lot)
            try:
                needle = normalize_plate(target)
            except InvalidPlateError:
                needle = (target or "").strip().upper()
                
            seq_matches, seq_comps = sequential_search(records, "plate", needle)
            
            sorted_copy, sort_stats = merge_sort(list(records), "plate")
            index, bin_comps = binary_search(sorted_copy, "plate", needle)

            if index >= 0:
                st.success("✅ Vehicle Found (Exact Match)!")
                st.dataframe([sorted_copy[index]], use_container_width=True, hide_index=True)
            elif seq_matches:
                st.info("✅ Partial Matches Found:")
                st.dataframe(seq_matches, use_container_width=True, hide_index=True)
            else:
                st.error("❌ Vehicle not found in the system.")

            with st.expander("⚙️ Technical Algorithm Details (For Defense)", expanded=False):
                st.markdown("**Sequential Search:**")
                st.write(f"- Matches found: `{len(seq_matches)}`")
                st.write(f"- Operations (Comparisons): `{seq_comps}`")
                
                st.markdown("**Binary Search:**")
                st.write(f"- Target Index: `{index}`")
                st.write(f"- Operations (Comparisons): `{bin_comps}`")
                
                st.markdown("**Pre-sorting (Merge Sort):**")
                st.write(f"- Sort Comparisons: `{sort_stats.get('comparisons', 0)}`")
                st.write(f"- Recursive Calls: `{sort_stats.get('recursive_calls', 0)}`")