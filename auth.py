import streamlit as st
import streamlit_authenticator as stauth
import pickle
from pathlib import Path

import yaml
from yaml.loader import SafeLoader
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