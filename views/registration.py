import streamlit as st
import datetime

st.title("Welcome")

# -----------------------------
# Helpers
# -----------------------------

PROFILE_KEYS_TO_CLEAR = [
    # Final resolved profile
    "user_dob",
    "user_gender",
    "user_height",
    "user_weight",

    # Form-source profile
    "form_dob",
    "form_gender",
    "form_height",
    "form_weight",

    # AI-source profile
    "ai_age",
    "ai_dob",
    "ai_gender",
    "ai_height",
    "ai_weight",
    "ai_diets",

    # Diet/macro state
    "selected_diets",
    "diet_profile",
    "target_calories",
    "target_macros",

    # AI commentary cache
    "ai_commentary",
    "commentary_signature",
]


def clear_profile_state():
    """
    Clears old profile data so previous attempts do not leak into a new flow.
    """
    for key in PROFILE_KEYS_TO_CLEAR:
        st.session_state.pop(key, None)

    # Clear conflict radio selections too
    for key in list(st.session_state.keys()):
        if key.startswith("choice_"):
            st.session_state.pop(key, None)


tab1, tab2 = st.tabs(["Log In", "Sign Up"])

# -----------------------------
# Log In
# -----------------------------
with tab1:
    st.subheader("Welcome Back")

    login_email = st.text_input("Email", key="login_email")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log In", use_container_width=True):
        if login_email and login_password:
            st.session_state.logged_in = True
            st.session_state.user_email = login_email

            # In a real app, you would load saved profile data here.
            st.switch_page("views/main_menu.py")
        else:
            st.error("Please enter both email and password.")


# -----------------------------
# Sign Up
# -----------------------------
with tab2:
    st.subheader("Create Account")

    signup_name = st.text_input("Full Name (Optional)", key="signup_name")
    signup_email = st.text_input("Email Address", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")

    signup_dob = st.date_input(
        "Date of Birth (Optional)",
        value=None,
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.date.today(),
        key="signup_dob"
    )

    signup_gender = st.selectbox(
        "Biological Sex (Optional, for BMR)",
        options=["Select", "Male", "Female"],
        key="signup_gender"
    )

    signup_height = st.number_input(
        "Height (cm) (Optional)",
        value=None,
        min_value=50.0,
        max_value=300.0,
        step=1.0,
        key="signup_height"
    )

    signup_weight = st.number_input(
        "Weight (kg) (Optional)",
        value=None,
        min_value=20.0,
        max_value=300.0,
        step=1.0,
        key="signup_weight"
    )

    is_metrics_filled = bool(
        signup_dob
        and signup_gender != "Select"
        and signup_height
        and signup_weight
    )

    col1, col2, col3 = st.columns(3)

    # -----------------------------
    # Simple Register
    # -----------------------------
    with col1:
        if st.button("Register", use_container_width=True):
            if signup_email and signup_password:
                clear_profile_state()

                st.session_state.logged_in = True
                st.session_state.user_name = signup_name
                st.session_state.user_email = signup_email
                st.session_state.diet_profile = "Unspecified"

                st.switch_page("views/main_menu.py")
            else:
                st.error("Email and Password are required.")

    # -----------------------------
    # Manual Setup
    # -----------------------------
    with col2:
        if st.button("Manual Setup", use_container_width=True, disabled=not is_metrics_filled):
            if signup_email and signup_password:
                clear_profile_state()

                st.session_state.logged_in = True
                st.session_state.user_name = signup_name
                st.session_state.user_email = signup_email

                # Manual setup writes directly to the final resolved profile.
                st.session_state.user_dob = signup_dob
                st.session_state.user_gender = signup_gender
                st.session_state.user_height = float(signup_height)
                st.session_state.user_weight = float(signup_weight)

                st.session_state.selected_diets = []

                st.switch_page("views/personalization.py")
            else:
                st.error("Email and Password are required.")

    # -----------------------------
    # AI Consult
    # -----------------------------
    with col3:
        if st.button("AI Consult", use_container_width=True):
            if signup_email and signup_password:
                clear_profile_state()

                st.session_state.logged_in = True
                st.session_state.user_name = signup_name
                st.session_state.user_email = signup_email

                # Important:
                # Save signup form entries as FORM-SOURCE values.
                # Do NOT write these to user_* yet.
                # personalization.py will compare form_* vs ai_*.
                if signup_dob:
                    st.session_state.form_dob = signup_dob

                if signup_gender != "Select":
                    st.session_state.form_gender = signup_gender

                if signup_height:
                    st.session_state.form_height = float(signup_height)

                if signup_weight:
                    st.session_state.form_weight = float(signup_weight)

                st.switch_page("views/consultation.py")
            else:
                st.error("Email and Password are required.")