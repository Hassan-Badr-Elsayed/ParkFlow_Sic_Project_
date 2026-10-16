import streamlit as st

st.set_page_config(page_title="ParkFlow | Smart Parking", page_icon="🚘", layout="wide", initial_sidebar_state="expanded")

def apply_pro_theme():
    st.markdown("""
        <style>
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .block-container {padding-top: 2rem !important; max-width: 1200px;}

        /* خلفية التطبيق */
        .stApp {
            background-color: #f0f4f8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* تنسيق كارت تسجيل الدخول (Form) */
        [data-testid="stForm"] {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            border: 1px solid #e1e8ed;
        }

        /* تنسيق الأزرار الاحترافية */
        .stButton > button, [data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border-radius: 12px;
            border: none;
            padding: 12px 24px;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 123, 255, 0.3);
            color: #ffffff;
        }

        /* تنسيق الكروت الإحصائية (Metrics) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e1e8ed;
            text-align: center;
        }
        div[data-testid="stMetricValue"] {
            color: #007bff;
            font-size: 2.5rem;
            font-weight: 900;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 1.1rem;
            color: #6c757d;
            font-weight: 600;
        }

        /* حقول الإدخال */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #e1e8ed;
            padding: 12px 15px;
            font-size: 15px;
            color: #2c3e50 !important;
            background-color: #f8f9fa !important;
            transition: all 0.3s;
        }
        .stTextInput > div > div > input:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
        }

        /* تنسيق النصوص الترحيبية */
        .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            color: #1a202c;
            line-height: 1.2;
            margin-bottom: 10px;
        }
        .hero-subtitle {
            font-size: 1.3rem;
            color: #4a5568;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_theme()

from ui.state import get_current_user, init_state
from ui.auth import render_landing_page, render_sidebar
from ui.dashboard_tab import render_dashboard_tab
from ui.driver_tab import render_driver_tab
from ui.history_tab import render_history_tab
from ui.operations_tab import render_operations_tab

init_state()
#############################################################################################################
if st.session_state.get("current_user") is None:
    try:
        from ui.state import get_user_manager
        params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
        
        if "user" in params:
            saved_user = params["user"]
            if isinstance(saved_user, list):
                saved_user = saved_user[0] 
                
            um = get_user_manager()
            st.session_state["current_user"] = um.get_user(saved_user)
    except Exception:
        pass

############################################################################################################
user = get_current_user()
if user is None:
    render_landing_page()
    st.stop()

render_sidebar()
role = str(getattr(user, "role", "")).lower()

st.markdown(f"<h2>Welcome back, {user.username} 👋</h2>", unsafe_allow_html=True)

if role == "admin":
    tabs = st.tabs(["📊 Dashboard", "🕒 History", "⚙️ Operations", "🚗 Driver Portal"])
    with tabs[0]: render_dashboard_tab()
    with tabs[1]: render_history_tab()
    with tabs[2]: render_operations_tab()
    with tabs[3]: render_driver_tab()
elif role == "employee":
    tabs = st.tabs(["⚙️ Operations", "🕒 History"])
    with tabs[0]: render_operations_tab()
    with tabs[1]: render_history_tab()
elif role in ("customer", "driver"):
    tabs = st.tabs(["🚗 Driver Portal"])
    with tabs[0]: render_driver_tab()
    
else:
    st.error(f"Unknown role: {user.role}")