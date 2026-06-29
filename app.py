import streamlit as st

st.set_page_config(page_title="Selective Diet", initial_sidebar_state="collapsed")

# Initialize Auth State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- The Lock Screen ---
if not st.session_state.authenticated:
    st.title("🔒 Restricted Access")
    password = st.text_input("Enter Prototype Password", type="password")
    if st.button("Unlock"):
        # Use st.secrets for the password, NEVER hardcode it here
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# 1. Page Config must be the very first Streamlit command
st.set_page_config(
    page_title="Selective Diet",
    page_icon="🍏",
    initial_sidebar_state="collapsed" # Starts the sidebar hidden like a mobile drawer
)

# 2. Inject CSS to hide all Streamlit web branding and headers
st.markdown("""
    <style>
        /* Hide the top colored decoration line */
        div[data-testid="stDecoration"] {
            display: none;
        }
        /* Hide the top header bar (hamburger menu & deploy button) */
        header {
            visibility: hidden;
        }
        /* Hide the default Streamlit footer */
        footer {
            visibility: hidden;
        }
        /* Pull the main content up to remove the massive top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session States
if "diet_profile" not in st.session_state:
    st.session_state.diet_profile = None

# 4. Define Navigation Routing
registration_page = st.Page("views/registration.py", title="Identity Select")
consultation_page = st.Page("views/consultation.py", title="AI Consultation")
personalization_page = st.Page("views/personalization.py", title="Diet Personalization")
main_menu_page = st.Page("views/main_menu.py", title="Dashboard")
restaurant_page = st.Page("views/restaurant_track.py", title="Restaurants")
grocery_page = st.Page("views/grocery_track.py", title="Groceries")

# 5. Run App
pg = st.navigation([
    registration_page,
    consultation_page, 
    personalization_page, 
    main_menu_page, 
    restaurant_page, 
    grocery_page
])
pg.run()