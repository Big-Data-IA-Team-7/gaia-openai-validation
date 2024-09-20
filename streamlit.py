import streamlit as st
import json
from read import fetch_data_from_db
from openai_api_call import OpenAIClient
from datetime import datetime
from data_storage import insert_model_response
from streamlit_custom_css import apply_custom_css
from streamlit_home_page import render_home_page
from streamlit_dashboard_page import render_dashboard_page
from streamlit_predicting_page import render_predicting_page
from streamlit_predicting_page import reset_interaction_state


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
        reset_interaction_state()  # Reset the interaction state when navigating to the Home page
    if st.sidebar.button("Predicting"):
        st.session_state.page = "Predicting"
        reset_interaction_state()  # Reset the interaction state when navigating to the Predicting page
        reset_interaction_state()  # Reset the interaction state when navigating to the Predicting page
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "Dashboard"
        reset_interaction_state()  # Reset the interaction state when navigating to the Dashboard page

def download_file(url):
    # Parse the URL to extract the file name
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    filename = os.path.basename(path)
    extension = os.path.splitext(filename)[1]
    
    # Create a temporary file with the correct extension
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    
    # Get the file from the URL
    response = requests.get(url)
    response.raise_for_status()  # Check if the download was successful
    
    # Write the content to the temporary file
    temp.write(response.content)
    temp.close()  # Close the file to finalize writing
    
    return temp.name  # Return the path to the temporary file

def main():
    """Main function to control the flow of the app."""
    apply_custom_css()
    setup_session_state()

    openai_client = OpenAIClient()

    openai_client = OpenAIClient()
    
    # Call the function and store the result in a DataFrame
    data_frame = fetch_data_from_db()

    render_sidebar()

    if st.session_state.page == "Home":
        render_home_page()
    elif st.session_state.page == "Predicting":
        if data_frame is not None:
            render_predicting_page(data_frame, openai_client)
            render_predicting_page(data_frame, openai_client)
        else:
            st.write("Failed to retrieve data")
    elif st.session_state.page == "Dashboard":
        render_dashboard_page()

if __name__ == "__main__":
    main()
