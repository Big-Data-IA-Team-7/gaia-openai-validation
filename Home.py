from dotenv import load_dotenv
load_dotenv()

from project_logging import logging_module

import streamlit as st

if 'home_page' not in st.session_state:
    st.session_state.home_page = 'home' 
    logging_module.log_success("NEW PROGRAM EXECUTION\n\n")

# Render the Home page content.
st.title("OpenAI Benchmarking with GAIA")
st.header("Group Members", divider="gray")

members = ["Pragnesh Anekal", "Ram Kumar Ramasamy Pandiaraj", "Dipen Patel", "Ramy Solanki"]

for i in range(len(members)):
    st.markdown(str(i+1) + ". " + members[i])