import streamlit as st

from core.sorting import compare_sorts, insertion_sort, merge_sort
from ui.state import get_lot


SORT_FIELDS = ["plate", "vehicle_type", "entry_time", "exit_time", "fee", "floor", "slot"]


def _history_records(lot):
    records = []
    for session in lot.get_history():
        data = session.to_dict()
        data["fee"] = float(data.get("fee") or 0)
        records.append(data)
    return records


def render_history_tab():
    lot = get_lot()
    records = _history_records(lot)

    st.subheader("Parking history")
    st.caption("Sort closed sessions with insertion sort or merge sort, or compare both.")

    if not records:
        st.info("No closed sessions in history yet.")
        return

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        field = st.selectbox("Sort field", SORT_FIELDS, index=2)
    with col_b:
        order = st.radio("Order", ["ascending", "descending"], horizontal=True)
    with col_c:
        algorithm = st.selectbox(
            "Algorithm",
            ["insertion_sort", "merge_sort", "compare_sorts"],
        )
    with col_d:
        st.write("")
        st.write("")
        run = st.button("Sort", key="hist_sort")

    reverse = order == "descending"

    if not run:
        st.dataframe(records, use_container_width=True, hide_index=True)
        return

    if algorithm == "insertion_sort":
        sorted_rows, stats = insertion_sort(records, field, reverse=reverse)
        st.dataframe(sorted_rows, use_container_width=True, hide_index=True)
        st.markdown("**insertion_sort metrics**")
        st.json(
            {
                "comparisons": stats.get("comparisons", 0),
                "shifts": stats.get("shifts", 0),
            }
        )
    elif algorithm == "merge_sort":
        sorted_rows, stats = merge_sort(records, field, reverse=reverse)
        st.dataframe(sorted_rows, use_container_width=True, hide_index=True)
        st.markdown("**merge_sort metrics**")
        st.json(
            {
                "comparisons": stats.get("comparisons", 0),
                "recursive_calls": stats.get("recursive_calls", 0),
            }
        )
    else:
        insertion_rows, insertion_stats = insertion_sort(records, field, reverse=reverse)
        merge_rows, merge_stats = merge_sort(records, field, reverse=reverse)
        comparison = compare_sorts(records, field, reverse=reverse)
        st.markdown("**Sorted table (merge_sort)**")
        st.dataframe(merge_rows, use_container_width=True, hide_index=True)
        left, right = st.columns(2)
        with left:
            st.markdown("**insertion_sort**")
            st.json(
                {
                    "comparisons": insertion_stats.get("comparisons", 0),
                    "shifts": insertion_stats.get("shifts", 0),
                }
            )
        with right:
            st.markdown("**merge_sort**")
            st.json(
                {
                    "comparisons": merge_stats.get("comparisons", 0),
                    "recursive_calls": merge_stats.get("recursive_calls", 0),
                }
            )
        st.write(
            f"Same result: **{comparison.get('same_result')}** "
            f"(insertion vs merge row lists)."
        )
        if insertion_rows != merge_rows:
            st.markdown("**insertion_sort table**")
            st.dataframe(insertion_rows, use_container_width=True, hide_index=True)
