import streamlit as st
import streamlit_authenticator as stauth 
from pathlib import Path
import pandas as pd
import logging
from core.sql.user_authentication import register_new_user_query
from core.duckdb_connector import *
from core.utils import handle_exception
import yaml
from yaml.loader import SafeLoader

USER_PROFILES_TABLE_ID = "ilab.main.user_details"
logging.basicConfig(level=logging.INFO)

class Authenticator:
    def __init__(self) -> None:
        self.conn = DuckdbConnector()
        self.jinja_environment = jinja2.Environment()

    def _query_users_info_from_database(self, result_format='list'):

        sql_query = """
        SELECT *
        FROM {{table_id}}
        """

        query_template = self.jinja_environment.from_string(sql_query)
        
        query = query_template.render(
            table_id = USER_PROFILES_TABLE_ID
        )

        query_result = self.conn.run_query(
            sql=query,
            result_format=result_format
        )

        logging.info("Finished querying users info from the database")
        return query_result
    
    def _authenticate_user(self):

        # Open config.yaml file
        with open('./config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)

        # Query all users from the database
        query_result = self._query_users_info_from_database(result_format='list')

        # Empty dictionary for Authenticate to read
        credentials_from_database = {
            "credentials": {
                "usernames": {}}
            }

        # Inserting users into the empty dictionary
        for user in query_result:
            username = user[0]
            name = user[1]
            email = user[2]
            password = user[5]

            credentials_from_database["credentials"]["usernames"][username] = {
                "email": email,
                "logged_in": False,
                "name": name,
                "password": password
            }

        # Initializing Authenticate
        authenticator = stauth.Authenticate(
            credentials_from_database['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )

        return authenticator

    @handle_exception(has_random_message_printed_out=True)
    def user_login(self,layout_position=st):

        # Check if is existing user and then login
        #if key is None:
        authenticator = self._authenticate_user()
        name, authentication_status, username = authenticator.login()
        #else:
        #    name, authentication_status, username = self.authenticator.login(fields={'Form name':key})

        if authentication_status != False:
            logging.info("Login successful")
        else:
            logging.info("Incorrect username or password")
            layout_position.write("Incorrect username or password")

        return name, authentication_status, username

    def insert_user_info_into_database(self, username, name, email, age, gender, password):

        query_template = self.jinja_environment.from_string(register_new_user_query)

        query = query_template.render(
            table_id = USER_PROFILES_TABLE_ID
        )

        parameters = {
            'username': username,
            'name': name,
            'email': email,
            'age': age,
            'gender': gender.lower(),
            'password': password
        }

        self.conn.run_query(
            sql=query,
            parameters=parameters
        )
        logging.info("Successfully inserted user info into the database")

    @handle_exception(has_random_message_printed_out=True)
    def new_user_registration(self, layout_position=st):

        # Sign up page
        with layout_position.expander("Sign up"):
            with st.form('Sign up',clear_on_submit=True):    

                # Extract user information
                username = st.text_input('Username')
                name = st.text_input('Name')
                email = st.text_input('Email')
                age = st.slider('Age', 1, 120, 18)
                gender = st.selectbox('How would you describe your gender?', ('Male', 'Female', 'Other'))
                password = st.text_input('Password', type='password')
                re_password = st.text_input('Repeat password', type='password')

                # Check if existing user, check re_password and then save user info into the database
                submitted = st.form_submit_button('Submit')
                if submitted:
                    # Extract existing usernames and emails from the database
                    query_result = self._query_users_info_from_database(result_format='dataframe')
                    usernames_and_emails = query_result[['username', 'email']]
                    if (username in usernames_and_emails['username'].values or email in usernames_and_emails['email'].values):
                        st.write("username or email already exist")
                    else:    
                        if password and re_password:
                            if password == re_password:
                                st.write(f"Hi {name}, you have successfully registered!")
                                self.insert_user_info_into_database(username, name, email, age, gender, password)
                            else:
                                st.write("Passwords entered do not match")
                        else:
                            st.write("Please enter your password")
