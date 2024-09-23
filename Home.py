from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Render the Home page content.
st.title("OpenAI Benchmarking with GAIA")
st.header("Group Members", divider="gray")

members = ["Pragnesh Anekal", "Ram Kumar Ramasamy Pandiaraj", "Dipen Patel", "Ramy Solanki"]

for i in range(len(members)):
    st.markdown(str(i+1) + ". " + members[i])