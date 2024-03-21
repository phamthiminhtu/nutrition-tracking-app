
import streamlit as st
import streamlit_authenticator as stauth 
#pip install streamlit-authenticator==0.1.5 
import duckdb
import pickle
from pathlib import Path
import pandas as pd
import logging

from core.duckdb_connector import *
#from duckdb_connector import *

from core.utils import handle_exception
#from utils import handle_exception
logging.basicConfig(level=logging.INFO)
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

class Authenticator:
    def __init__(self) -> None:
        self.conn = DuckdbConnector()
        
    logging.info("----------- Running get_user_personal_data()-----------")
    def log_in(self) -> bool:
        "return yes, no and none for auth status"
        #self.conn.create_users_table()
        users = self.conn.fetch_users()
        self.authenticator = stauth.Authenticate(config['credentials'],cookie_name='some',key='sesame')
        usernames = [user[1] for user in users]
        passwords = [user[2] for user in users]
        user_ids = [user[0] for user in users]
        name, authentication_status, username = self.authenticator.login( 'main')
        return True;
    @handle_exception(has_random_message_printed_out=True)
    def register_user(self):
        try:
            user_id, username, name_of_registered_user = self.authenticator.register_user(preauthorization=False,fields={'Form name':'Register user', 'User ID':'user_id', 'Username':'username','Age':'age','Gender':'gender', 'Password':'password', 'Repeat password':'Repeat password', 'Register':'Register'})
            #self.conn.insert_user({'user_id':user_id, 'gender':gender})
            if user_id:
                st.success('User registered successfully')
        except Exception as e:
            st.error(e)
#
#auth = Authenticator()
#auth.log_in()
#auth.register_user()


"""if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password') """