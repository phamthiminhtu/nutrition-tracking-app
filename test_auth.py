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

db = DuckdbConnector()
auth = Authenticator()
#db.create_users_table()
#res = db.insert_user({
#            "user_id": "tu@gmail.com",
#            "gender": "female",
#            "age": 20.0,
#            "username": "Tu",
#            "password": "Protein"
#        })
#db.insert_user({
#            "user_id": "nyan@gmail.com",
#            "gender": "male",
#            "age": 26,
#            "username": "Tyler",
#            "password": "Vitamin A"
#        })
#print(res)
#print(db.fetch_users())
auth.log_in()
#auth.register_user()