
import streamlit as st
import streamlit_authenticator as stauth 
#pip install streamlit-authenticator==0.1.5 
import duckdb
import pickle
from pathlib import Path
import pandas as pd
import logging

from core.duckdb_connector import *
from core.sql.user_authentication import *

from core.utils import handle_exception
logging.basicConfig(level=logging.INFO)
class Authenticator:
    def __init__(self) -> None:
        self.conn = DuckdbConnector()

    @handle_exception(has_random_message_printed_out=True)
    def create_users_table(self)->bool:
        self.users_table_database = self.conn.run_query(sql=create_user_profiles_query)
        if self.users_table_database!=None:
            print('users table created')
            return True
        else:
            return False
    def insert_user(self,
                    user_info_df:str,
                    user_info:dict)->None:
        query_template = self.jinja_environment.from_string(
            register_new_user_query
        )
        query = query_template.render(
            table_id=USER_PROFILES_TABLE_ID,
            temp_user_df = user_info_df
        )
        parameters = {
            "user_id": user_info.get("user_id"),
            "gender": user_info.get("gender"),
            "age": user_info.get("age"),
            "username": user_info.get("username"),
            "password":user_info.get("password")
        }
        self.user_insert_stat = self.conn.run_query(
            sql=query,
            parameters=parameters
        )
        if not self.user_insert_stat:
            print("Not inserted")
        else:
            print("Inserted")
    def fetch_users(self)->dict:
        query_template = self.jinja_environment.from_string(
            get_users_query
        )
        query = query_template.render(
            table_id=USER_PROFILES_TABLE_ID,
        )
        self.all_users = self.conn.run_query(
            sql=query,
        )
        return self.all_users
    logging.info("----------- Running get_user_personal_data()-----------")
    def log_in(self) -> bool:
        "return yes, no and none for auth status"
        user_df = pd.DataFrame([
                {
                    "user_id": "tu@gmail.com",
                    "gender": "female",
                    "age": 20,
                    "username": "tu",
                    "password": "Protein"
                },
                {
                    "user_id": "nyan@gmail.com",
                    "gender": "male",
                    "age": 26,
                    "username": "beef burger",
                    "password": "Vitamin A"
                }]
        )
        self.create_users_table()
        self.insert_user("user_df",user_df[0])
        users = self.fetch_users()
        usernames = [user['username'] for user in users]
        passwords = [user['password'] for user in users]
        user_ids = [user['user_id'] for user in users]
        authenticator = stauth.Authenticate(user_ids, usernames,passwords,'nutrients_dashboard','abcd')
        name, authentication_status, username = authenticator.login('Login', 'main')
        return True;

auth = Authenticator.log_in()

""" 
name, authentication_status, username = authenticator.login('Login', 'main')


if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password') """