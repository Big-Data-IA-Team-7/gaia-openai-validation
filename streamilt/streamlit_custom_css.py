import streamlit as st

def apply_custom_css():
    """Apply custom CSS for button styling."""
    custom_css = """
    <style>
    .stButton > button {
        width: 200px; /* Adjust the width */
        height: 50px; /* Adjust the height */
        font-size: 16px; /* Adjust the font size */
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)