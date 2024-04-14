import streamlit as st
import streamlit_authenticator as stauth 
from pathlib import Path
import pandas as pd
import logging
from core.sql.user_authentication import register_new_user_query_2nd_version
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
        self.authenticator = self._authenticate_user()

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
    def user_login(self, layout_position=st):

        # Check if is existing user and then login
        name, authentication_status, username = self.authenticator.login()

        if authentication_status != False:
            logging.info("Login successful")
        else:
            logging.info("Incorrect username or password")
            layout_position.write("Incorrect username or password")

        return name, authentication_status, username

    def insert_user_info_into_database(self, username, name, email, age, gender, password):

        query_template = self.jinja_environment.from_string(register_new_user_query_2nd_version)

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

        # Extract existing usernames and emails from the database
        query_result = self._query_users_info_from_database(result_format='dataframe')
        usernames_and_emails = query_result[['username', 'email']]

        # Sign up page
        with layout_position.expander("Sign up"):
            with st.form('Sign up'):    

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











# class Authenticator:
#     def __init__(self) -> None:
#         with open('config.yaml') as file:
#             self.config = yaml.load(file, Loader=SafeLoader)
#         self.conn = DuckdbConnector()
#         self.users = self.conn.fetch_users()
#         #print(users)
#         #print("og config________",config['credentials'])
#         self.config['cookie']={'expiry_days': 0, 'key': 'abcdefqwe', 'name': 'choc_cookie'}
#         self.config['credentials']['usernames']={}
#         if self.users:
#             for username, (username, user_id, password) in enumerate(self.users):
#                 self.config['credentials']['usernames'][username] = {'email': user_id,'logged_in': False, 'name': username, 'password':password}
#         self.authenticator = stauth.Authenticate(self.config['credentials'],self.config['cookie']['name'],self.config['cookie']['key'],self.config['cookie']['expiry_days'])

#     logging.info("----------- Running log_in()-----------")
#     @handle_exception(has_random_message_printed_out=True)
#     def log_in(self):
#         "return yes, no and none for auth status"
#         self.name,self.authentication_status, self.username = self.authenticator.login(location='sidebar')
#         logging.info("----------- finish loggedin----------")
#         return self.name, self.authentication_status, self.username
#     @handle_exception(has_random_message_printed_out=True)
#     def log_out(self):
#             self.authenticator.logout(location='unrendered')
#             logging.info("----------- finish logged out----------")
#     @handle_exception(has_random_message_printed_out=True)
#     def get_user_id(self,username):
#         result = self.conn.get_user_id(username)
#         #print(result[0][0])
#         return result[0][0]
#     @handle_exception(has_random_message_printed_out=True)
#     def register_user_form(self):
#         with st.form("sign_up_form"):
#             st.write("Register new user")
#             user_id = st.text_input('User Id / Email')
#             username = st.text_input('Username')
#             slider_age = st.slider("Age slider")
#             gender_option = st.selectbox('How would you describe your gender?',
#                             ('Male', 'Female', 'Other'))
#             password = st.text_input('Password',type='password')
#             re_password = st.text_input('Repeat password',type='password')
#             # Every form must have a submit button.
#             submitted = st.form_submit_button("Submit")
#             if submitted:
#                 if password==re_password:
#                     st.write("age", slider_age, "userID", user_id, 'username',username,'password',password)
#                     new_user_df = {"user_id": user_id,
#                                 "gender": gender_option,
#                                 "age": slider_age,
#                                 "username": username,
#                                 "password": password
#                                 }   
#                     self.conn.insert_user(new_user_df)