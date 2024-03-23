import streamlit as st
import streamlit_authenticator as stauth 
#pip install streamlit-authenticator==0.1.5 
import duckdb
import logging
from core.auth import *
from core.duckdb_connector import *
#logging.basicConfig(level=logging.INFO)

st.set_page_config(layout='wide')


user_profiles_temp = pd.DataFrame(
    [
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20.0,
            "username": "Tu",
            "password": "Protein"
        },
        {
            "user_id": "nyan@gmail.com",
            "gender": "male",
            "age": 26,
            "username": "Tyler",
            "password": "Vitamin A"
        }
    ]
)
#print(user_profiles_temp['user_id'])

db = DuckdbConnector()
#user_profiles_temp = db.fetch_users()
#print(user_profiles_temp)
auth = Authenticator()
#db.create_users_table()
inse=False
if inse!=True:
    #db.create_users_table()
    #res = db.insert_user({"user_id": "nyan@gmail.com","gender": "male","age": 26,"username": "Tyler","password": "Vitamin A"})
    #res2 = db.insert_user({"user_id": "tu@gmail.com","gender": "female","age": 20.0,"username": "Tu","password": "Protein"})
    inse=True
#print(res)
#print(db.fetch_users())
print(auth.log_in())
#auth.register_user_form()
auth.log_out()
if 'button' not in st.session_state:
    st.session_state.button = False

def click_button():
    st.session_state.button = not st.session_state.button

st.button('Register new user', on_click=click_button)

if st.session_state.button:
    # The message and nested widget will remain on the page
    auth.register_user_form()
