import streamlit as st

if "step" not in st.session_state:
    st.session_state.step = "registration"
if "diet_profile" not in st.session_state:
    st.session_state.diet_profile = None

if st.session_state.step == "registration":
    st.title("Welcome to Selective Diet")
    st.subheader("Select Your Dietary Profile to Initialize Session Variable")
    
    profiles = ["Halal", "Keto/Low-Carb", "Low-GI", "Temple Food", "Gluten-Free"]
    selected = st.radio("Choose a profile:", profiles)
    
    if st.button("Confirm Profile & Enter"):
        st.session_state.diet_profile = selected
        st.session_state.step = "main_menu"
        st.rerun()

elif st.session_state.step == "main_menu":
    st.title(f"Main Menu [{st.session_state.diet_profile} Mode Active]")
    st.write("Downstream raw data fields filtered via Auditing Matrix.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("Restaurant Track")
        st.write("Ready-to-eat curated meals")
        if st.button("Go to Restaurants"):
            st.session_state.step = "restaurant_track"
            st.rerun()
            
    with col2:
        st.header("Groceries Track")
        st.write("Shoppable recipes & direct SKUs")
        if st.button("Go to Groceries"):
            st.session_state.step = "grocery_track"
            st.rerun()

elif st.session_state.step == "restaurant_track":
    st.title(f"Local Restaurant Fulfillment ({st.session_state.diet_profile})")
    st.write("Order manifest pushed to local kitchen tablet interface.")
    
    if st.button("Simulate Checkout (Trigger B2B Delivery API)"):
        st.success("API Webhook Triggered: Barogo/Vroong courier assigned programmatically.")
        st.info("Transactional call utility fee processed. Company liability: 0%")
        
    if st.button("Back to Main Menu"):
        st.session_state.step = "main_menu"
        st.rerun()

elif st.session_state.step == "grocery_track":
    st.title("Shoppable Recipes & Curated Groceries")
    st.write("Backend converting text components into precise retail SKUs.")
    
    if st.button("Sync Cart (Trigger E-Groceries API)"):
        st.success("Deep-links programmatically generated for Coupang Partners / Kurly API.")
        st.warning("Client redirected to native e-commerce gateway. 3% commission captured.")
        
    if st.button("Back to Main Menu"):
        st.session_state.step = "main_menu"
        st.rerun()
