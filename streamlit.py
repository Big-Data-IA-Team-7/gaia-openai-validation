import streamlit as st
import json
from read import fetch_data_from_db

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
    if "button" not in st.session_state:
        st.session_state.button = False  # Default Button state

def render_sidebar():
    """Render the sidebar with navigation buttons."""
    st.sidebar.title("Navigation")
    if st.sidebar.button("Home"):
        st.session_state.page = "Home"
        st.session_state.button = False  # Reset the button on the home page
    if st.sidebar.button("Predicting"):
        st.session_state.page = "Predicting"
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "Dashboard"

def render_home_page():
    """Render the Home page content."""
    st.title("Assignment 1 (GAIA Dataset)")
    st.write("**Group Member**")
    st.write("1. Pragnesh Anekal")
    st.write("2. Ram Kumar Ramasamy Pandiaraj")
    st.write("3. Dipen Patel")

def render_predicting_page(data_frame):
    """Render the Predicting page content with a selectbox that initially shows no values."""
    
    # Initially show a placeholder value
    placeholder_text = "Select a Question"

    # Selectbox for the question, default is the placeholder
    question_selected = st.selectbox(
        'Select a Question', 
        options=[placeholder_text] + list(data_frame['Question']),  # Adding placeholder to the list of questions
        index=0  # Start with the placeholder selected
    )

    # Proceed only if the user selects a valid question (not the placeholder)
    if question_selected != placeholder_text:
        st.text_area("Selected Question:", question_selected)

        # Answer to the selected Question
        validate_answer = data_frame[data_frame['Question'] == question_selected]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.write('Selected Question Answer is:', validate_answer)

        # Steps to the selected Question
        steps = data_frame[data_frame['Question'] == question_selected]
        steps = steps['Annotator Metadata'].iloc[0]
        steps_dict = json.loads(steps)
        steps_text = steps_dict.get('Steps', 'No steps found')

        # Display steps in a text area
        st.text_area('Steps:', steps_text)

        #Button for Asking Question to GPT
        button_values=st.button('Ask GPT')
        if button_values:
            st.write('Hello i am GPT! Write code from here')
    else:
        st.write("Please select a valid question to proceed.")


def render_dashboard_page():
    """Render the Dashboard page content."""
    st.title("Dashboard")
    st.write("You are now on Dashboard page.")

def main():
    """Main function to control the flow of the app."""
    apply_custom_css()
    setup_session_state()
    
    # Call the function and store the result in a DataFrame
    data_frame = fetch_data_from_db()

    render_sidebar()

    if st.session_state.page == "Home":
        render_home_page()
    elif st.session_state.page == "Predicting":
        if data_frame is not None:
            render_predicting_page(data_frame)
        else:
            st.write("Failed to retrieve data")
    elif st.session_state.page == "Dashboard":
        render_dashboard_page()

if __name__ == "__main__":
    main()
