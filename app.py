from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from data.data_read import fetch_data_from_db,fetch_data_from_db_dashboards
from openai_api.openai_api_call import OpenAIClient
from streamlit_ui.streamlit_custom_css import apply_custom_css
from streamlit_ui.streamlit_home_page import render_home_page
from streamlit_ui.streamlit_dashboard_page import render_dashboard_page
from streamlit_ui.streamlit_predicting_page import render_predicting_page
from streamlit_ui.streamlit_predicting_page import reset_interaction_state


def setup_session_state():
    """Initialize session state variables."""
    if "page" not in st.session_state:
        st.session_state.page = "Home"  # Default page
    if "ask_gpt_clicked" not in st.session_state:
        st.session_state.ask_gpt_clicked = False
    if "show_next_steps" not in st.session_state:
        st.session_state.show_next_steps = False
    if "show_no_response" not in st.session_state:
        st.session_state.show_no_response = False
    if "show_reset_button" not in st.session_state:
        st.session_state.show_reset_button = False
    if "show_ask_gpt_again" not in st.session_state:
        st.session_state.show_ask_gpt_again = False
    if "previous_question" not in st.session_state:
        st.session_state.previous_question = None
    if "ai_response" not in st.session_state:
        st.session_state.ai_response = ""
    if "steps_text" not in st.session_state:
        st.session_state.steps_text = ""


def render_sidebar():
    """Render the sidebar with navigation buttons."""
    st.sidebar.title("Navigation")
    if st.sidebar.button("Home"):
        st.session_state.page = "Home"
        reset_interaction_state()  # Reset the interaction state when navigating to the Home page
    if st.sidebar.button("Predicting"):
        st.session_state.page = "Predicting"
        reset_interaction_state()  # Reset the interaction state when navigating to the Predicting page
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "Dashboard"
        reset_interaction_state()  # Reset the interaction state when navigating to the Dashboard page

def main():
    
    """Main function to control the flow of the app."""
    apply_custom_css()
    setup_session_state()

    openai_client = OpenAIClient()
    
    # Call the function and store the result in a DataFrame
    data_frame = fetch_data_from_db()
    data_frame_dashboard=fetch_data_from_db_dashboards()
    render_sidebar()

    if st.session_state.page == "Home":
        render_home_page()
    elif st.session_state.page == "Predicting":
        if data_frame is not None:
            render_predicting_page(data_frame, openai_client)
        else:
            st.write("Failed to retrieve data")
    elif st.session_state.page == "Dashboard":
        render_dashboard_page(data_frame_dashboard,data_frame)

if __name__ == "__main__":
    main()
