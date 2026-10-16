import streamlit as st
from core.exceptions import AuthenticationError, ParkFlowError
from ui.state import get_current_user, get_lot, init_state, set_current_user

def inject_minimal_css():
    st.markdown("""
        <style>
        /* تنسيق العنوان الرئيسي */
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            color: #1f2937 !important;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        .hero-title span {
            color: #0066cc !important;
        }
        .hero-subtitle {
            font-size: 1.1rem;
            color: #4b5563 !important;
            margin-bottom: 2rem;
        }

        /* إصلاح الألوان المخفية (إجبار النصوص على اللون الداكن) */
        [data-testid="stMetricLabel"] *, 
        .stTextInput label p, 
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span,
        [data-testid="stForm"] h4,
        [data-testid="stForm"] p,
        [data-testid="stCaptionContainer"] * {
            color: #1f2937 !important;
        }

        /* لون مميز للتاب النشط */
        .stTabs [aria-selected="true"] p, 
        .stTabs [aria-selected="true"] span {
            color: #0066cc !important;
            font-weight: bold;
        }

        /* تحسين شكل زر الإرسال */
        [data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #0066cc, #004c99) !important;
            color: white !important;
            border-radius: 6px;
            border: none;
            transition: 0.3s;
        }
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0, 102, 204, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

def render_landing_page():
    init_state()
    inject_minimal_css()
    lot = get_lot()
    
    st.write("<br>", unsafe_allow_html=True)

    col_text, col_form = st.columns([1.2, 0.8], gap="large")

    with col_text:
        st.markdown("<div class='hero-title'>Smart <span>ParkFlow</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-subtitle'>Next-generation parking management. Real-time availability, smart space allocation, and seamless tracking.</div>", unsafe_allow_html=True)
        
        st.markdown("### 🚘 Live Lot Status")
        occ = lot.get_occupancy()
        m1, m2, m3 = st.columns(3)
        m1.metric("Available", occ['free'])
        m2.metric("Occupied", occ['occupied'])
        m3.metric("Waiting", occ['waiting'])
        
        st.info("ℹ️ ParkFlow optimizes space allocation using real-time data structures.")

    with col_form:
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("#### Welcome Back")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Access Dashboard")

            if submitted:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    try:
                        from ui.state import get_user_manager
                        um = get_user_manager()
                        user = um.authenticate(username, password) 
                        set_current_user(user)
                        if hasattr(st, "query_params"):
                            st.query_params["user"] = user.username
                        else:
                            st.experimental_set_query_params(user=user.username)
                        st.rerun()
                    except AuthenticationError as err:
                        st.error("Invalid credentials. Please try again.")
                    except ParkFlowError as err:
                        st.error(str(err))
            
            st.caption("Demo: admin_boss, emp_john, cust_sarah")

        with tab_register:
            with st.form("register_form", clear_on_submit=True):
                st.markdown("#### Join ParkFlow")
                new_user = st.text_input("Username *", help="Minimum 3 characters.")
                new_email = st.text_input("Email Address (Optional)")
                new_phone = st.text_input("Phone Number *", help="Digits only (8 to 15 digits).")
                plate_num = st.text_input("Vehicle Plate (Optional)", help="3 to 8 alphanumeric characters (e.g. ABC123).")
                new_pass = st.text_input("Password *", type="password", help="Minimum 6 characters.")
                confirm_pass = st.text_input("Confirm Password *", type="password")
                reg_submitted = st.form_submit_button("Create Account")
                
            if reg_submitted:
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif not new_phone:
                    st.error("Phone number is required.")
                else:
                    try:
                        from ui.state import get_user_manager, save_all
                        um = get_user_manager()
                        
                        um.register_customer(username=new_user, password=new_pass, phone=new_phone, plate=plate_num, email=new_email)
                        
                        save_all()
                        st.success("Account created successfully! You can now Sign In.")
                    except ParkFlowError as err:
                        st.error(str(err))

def render_sidebar():
    user = get_current_user()
    if user is None:
        return

    lot = get_lot()
    occ = lot.get_occupancy()

    with st.sidebar:
        st.markdown(f"### 👤 {user.username.title()}")
        st.caption(f"Access Level: {user.role.upper()}")
        
        st.divider()
        st.markdown("#### 📊 Real-Time Lot")
        st.metric("Total Capacity", occ['total'])
        st.metric("Free Spaces", occ["free"])
        st.metric("Reserved", occ.get("reserved", 0))
        
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            set_current_user(None)
            
            if hasattr(st, "query_params"):
                st.query_params.clear()
            else:
                st.experimental_set_query_params()
            st.rerun()