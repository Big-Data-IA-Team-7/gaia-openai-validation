import streamlit as st
import json
from read import fetch_data_from_db
from openai_api_call import OpenAIClient
from datas3 import process_data_and_generate_url
import requests
import tempfile
import os
from urllib.parse import urlparse, unquote
import mimetypes

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

def reset_interaction_state():
    """Reset the button interaction states."""
    st.session_state.ask_gpt_clicked = False
    st.session_state.show_next_steps = False
    st.session_state.show_no_response = False
    st.session_state.show_reset_button = False
    st.session_state.show_ask_gpt_again = False
    st.session_state.ai_response = ""
    st.session_state.previous_question = None
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

def render_home_page():
    """Render the Home page content."""
    st.title("Assignment 1 (GAIA Dataset)")
    st.write("**Group Member**")
    st.write("1. Pragnesh Anekal")
    st.write("2. Ram Kumar Ramasamy Pandiaraj")
    st.write("3. Dipen Patel")

def render_predicting_page(data_frame, openai_client):
    """Render the Predicting page content with a selectbox that initially shows no values."""
    
    # Initially show a placeholder value
    placeholder_text = "Select a Question"

    # Selectbox for the question, default is the placeholder
    question_selected = st.selectbox(
        'Select a Question', 
        options=[placeholder_text] + list(data_frame['Question']),  # Adding placeholder to the list of questions
        index=0  # Start with the placeholder selected
    )

    # Reset interaction state if a new question is selected
    if question_selected != st.session_state.previous_question:
        reset_interaction_state()  # Reset the session state if the question changes
        st.session_state.previous_question = question_selected  # Update the session state with the new question

    # Proceed only if the user selects a valid question (not the placeholder)
    if question_selected != placeholder_text:
        st.text_area("Selected Question:", question_selected)
        # Answer to the selected Question
        validate_answer = data_frame[data_frame['Question'] == question_selected]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.write('Selected Question Answer is:', validate_answer)
        file_name=process_data_and_generate_url(question_selected)
        if file_name == 1:
            st.write('No file is associated with this question')
        else:
            file_path = download_file(file_name)
            st.write('download file:',file_name)
        # Button for Asking Question to GPT
        if not st.session_state.ask_gpt_clicked:  # Check if Ask GPT hasn't been clicked yet
            button_values = st.button('Ask GPT')
            if button_values:
                st.session_state.ask_gpt_clicked = True  # Set Ask GPT to True when clicked
                validation_content = openai_client.format_content(0, question_selected)
                if file_name != 1:
                   ai_response = openai_client.file_validation_prompt(file_path, openai_client.val_system_content, validation_content)
                else:
                   ai_response = openai_client.validation_prompt(openai_client.val_system_content, validation_content)
                st.session_state.ai_response = ai_response
                if ai_response not in validate_answer:
                    st.session_state.show_next_steps = False
                    st.session_state.show_no_response = False  # Reset the buttons' state
                else:
                    st.success("GPT Predicted correct Answer")

        if st.session_state.ask_gpt_clicked:
            ai_response = st.session_state.ai_response
            st.write(ai_response)
            if ai_response not in validate_answer:
                st.error("Sorry GPT Predicted Wrong answer. Do you need the steps?")

                # Show Yes and No buttons if they haven't been clicked yet
                if not st.session_state.show_next_steps and not st.session_state.show_no_response:
                    col1, col2 = st.columns(2)
                    with col1:
                        if not st.session_state.show_no_response:  # Only show "Yes" if "No" is not clicked
                            if st.button("Yes"):
                                st.session_state.show_next_steps = True  # Store Yes button click
                                st.session_state.show_no_response = False
                                st.session_state.show_reset_button = False
                                st.session_state.show_ask_gpt_again = True  # Show Ask GPT Again button
                    with col2:
                        if not st.session_state.show_next_steps:  # Only show "No" if "Yes" is not clicked
                            if st.button('No'):
                                # Reset all interaction states and rerun the app
                                reset_interaction_state()
                                st.experimental_rerun()

                # If "Yes" was clicked, show the next steps and hide the "No" button
                if st.session_state.show_next_steps:
                    steps = data_frame[data_frame['Question'] == question_selected]
                    steps = steps['Annotator Metadata'].iloc[0]
                    steps_dict = json.loads(steps)
                    steps_text = steps_dict.get('Steps', 'No steps found')
                    steps_question=st.text_area('Steps:', steps_text)
                    st.session_state.steps_text = steps_question

                # Show Ask GPT Again button if needed
                if st.session_state.show_ask_gpt_again:
                    if st.button("Ask GPT Again"):
                        ann_validation_content = openai_client.format_content(1, question_selected, st.session_state.steps_text)
                        if file_name != 1:
                            ann_ai_response = openai_client.file_validation_prompt(file_path, openai_client.ann_system_content, ann_validation_content)
                        else:
                            ann_ai_response = openai_client.validation_prompt(openai_client.ann_system_content, ann_validation_content)
                        st.write(ann_ai_response)
                        if ann_ai_response not in validate_answer:
                            print('validate_answer',validate_answer)
                            st.error("Sorry!!! GPT Unable to predict the correct Answer after the steps provided ")
                        else:
                            print('validate_answer',validate_answer)
                            st.success('GPT Predicted the correct Answer')
    else:
        st.write("Please select a valid question to proceed.")
        
def render_dashboard_page():
    """Render the Dashboard page content."""
    st.title("Dashboard")
    st.write("You are now on Dashboard page.")

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
    
    # Call the function and store the result in a DataFrame
    data_frame = fetch_data_from_db()

    render_sidebar()

    if st.session_state.page == "Home":
        render_home_page()
    elif st.session_state.page == "Predicting":
        if data_frame is not None:
            render_predicting_page(data_frame, openai_client)
        else:
            st.write("Failed to retrieve data")
    elif st.session_state.page == "Dashboard":
        render_dashboard_page()

if __name__ == "__main__":
    main()
