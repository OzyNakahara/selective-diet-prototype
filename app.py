import streamlit as st

registration_page = st.Page("views/registration.py", title="Identity Select", icon=":material/person:")
main_menu_page = st.Page("views/main_menu.py", title="Dashboard", icon=":material/dashboard:")
restaurant_page = st.Page("views/restaurant_track.py", title="Restaurants", icon=":material/restaurant:")
grocery_page = st.Page("views/grocery_track.py", title="Groceries", icon=":material/shopping_cart:")

pg = st.navigation([registration_page, main_menu_page, restaurant_page, grocery_page])
pg.run()