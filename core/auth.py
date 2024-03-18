
import streamlit as st
import streamlit_authenticator as stauth 
#pip install streamlit-authenticator==0.1.5 
import duckdb
import pickle
from pathlib import Path

import yaml
from yaml.loader import SafeLoader
from core.duckdb_connector import *
from core.sql.user_authentication import *

from core.utils import handle_exception

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
    def log_in() -> bool:
        "return yes, no and none for auth status"
        name, authentication_status, username = authenticator.login('Login', 'main')

names = ['nyan','micheal', 'tu']
usernames = ['nhtun', 'myaputra','tpham']
#passwords = ['abc','def','ghi']
passwords = ['XXX','XXX','XXX']

hashed_passwords = stauth.Hasher(passwords).generate()

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords,file)

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