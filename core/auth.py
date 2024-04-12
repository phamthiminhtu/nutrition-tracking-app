
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

class Authenticator:
    def __init__(self) -> None:
        with open('config.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)
        self.conn = DuckdbConnector()
        self.users = self.conn.fetch_users()
        #print(users)
        #print("og config________",config['credentials'])
        self.config['cookie']={'expiry_days': 0, 'key': 'abcdefqwe', 'name': 'choc_cookie'}
        self.config['credentials']['usernames']={}
        if self.users:
            for username, (username, user_id, password) in enumerate(self.users):
                self.config['credentials']['usernames'][username] = {'email': user_id,'logged_in': False, 'name': username, 'password':password}
        self.authenticator = stauth.Authenticate(self.config['credentials'],self.config['cookie']['name'],self.config['cookie']['key'],self.config['cookie']['expiry_days'])

    logging.info("----------- Running log_in()-----------")
    @handle_exception(has_random_message_printed_out=True)
    def log_in(self):
        "return yes, no and none for auth status"
        self.name,self.authentication_status, self.username = self.authenticator.login(location='sidebar')
        logging.info("----------- finish loggedin----------")
        return self.name, self.authentication_status, self.username
    @handle_exception(has_random_message_printed_out=True)
    def log_out(self):
            self.authenticator.logout(location='unrendered')
            logging.info("----------- finish logged out----------")
    @handle_exception(has_random_message_printed_out=True)
    def get_user_id(self,username):
        result = self.conn.get_user_id(username)
        #print(result[0][0])
        return result[0][0]
    @handle_exception(has_random_message_printed_out=True)
    def register_user_form(self):
        with st.form("sign_up_form"):
            st.write("Register new user")
            user_id = st.text_input('User Id / Email')
            username = st.text_input('Username')
            slider_age = st.slider("Age slider")
            gender_option = st.selectbox('How would you describe your gender?',
                            ('Male', 'Female', 'Other'))
            password = st.text_input('Password',type='password')
            re_password = st.text_input('Repeat password',type='password')
            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                if password==re_password:
                    st.write("age", slider_age, "userID", user_id, 'username',username,'password',password)
                    new_user_df = {"user_id": user_id,
                                "gender": gender_option,
                                "age": slider_age,
                                "username": username,
                                "password": password
                                }   
                    self.conn.insert_user(new_user_df)