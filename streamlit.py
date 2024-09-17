import streamlit as st
import json
from read import fetch_data_from_db

# Call the function and store the result in a DataFrame
data_frame = fetch_data_from_db()

# # Verify the data
# if data_frame is not None:
#     print(data_frame.head())
# else:
#     print("Failed to retrieve data")


# Define custom CSS to adjust button size
custom_css = """
    <style>
    .stButton > button {
        width: 200px; /* Adjust the width */
        height: 50px; /* Adjust the height */
        font-size: 16px; /* Adjust the font size */
    }
    </style>
"""

# Inject the custom CSS into the Streamlit app
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize session state for page tracking
if "page" not in st.session_state:
    st.session_state.page = "Home"  # Default page
    st.session_state.button = False
if "button" not in st.session_state:
    st.session_state.button = False # Default Button state


# Sidebar buttons for navigation
st.sidebar.title("Navigation")
if st.sidebar.button("Home"):
    st.session_state.page = "Home"
    st.session_state.button=False # Reset the button in the home page
if st.sidebar.button("Predicting"):
    st.session_state.page = "Predicting"
if st.sidebar.button("Dashboard"):
    st.session_state.page = "Dashboard"

# Show content based on the selected page (Home Page)
if st.session_state.page == "Home":
    st.title("Assignment 1 (GAIA Dataset)")
    st.write("**Group Member**")
    st.write("1. Pragnesh Anekal")
    st.write("2. Ram Kumar Ramasamy Pandiaraj")
    st.write("3. Dipen Patel")
    
# This is the Second Page (Predication)
elif st.session_state.page=='Predicting':
    st.title("")
    # Selecting the Question
    Question_Selected=st.selectbox('Select a Question', data_frame['Question'])
    text_box_display=st.text_area("Selected Quesiton:",Question_Selected)

    #Answer to the selected Question
    validate_answer=data_frame[data_frame['Question']==Question_Selected]
    validate_answer=validate_answer['Final answer'].iloc[0]
    display_validate_answer=st.write('Selected Question Answer is:',validate_answer)

    #Steps to the selected Question
    steps=data_frame[data_frame['Question']==Question_Selected]
    steps=steps['Annotator Metadata'].iloc[0]
    text_steps=st.text_area('Steps:',steps)

    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    # Display steps in a text area
    text_steps_new = st.text_area('Steps:', steps_text)


# #This is for the second page    
# elif st.session_state.page == "Predicting":
#     st.title("")
#     first_question=st.text_input('Enter the Question')
#     first_answer=st.button('Ask the question')
#     if first_answer:
#         if first_question=='Dipen':
#             st.write('Yes! the Answer is Correct')
#             st.session_state.button=True # Reset the button in the home page
#         else:
#             st.write('No!!! it is Wrong Answer. Please provide additional details')
#             second_question=st.text_input("Enter More details:")
#             second_answer=st.button('Enter')
#             # print('Value of button',st.session_state.button)
#             # print('value of Second Answer',second_answer)
#             #condition for displaying the second button
#             if st.session_state.button==False & second_answer==True:
#                 print('Value of Second_answer',second_answer)
#                 if second_answer==False:
#                     print('Yes i am inside the second answer')
#                     if second_question=='Dipen':
#                         st.write("Correct answer")
#                     else:
#                         st.write('Wrong Answer')
            
elif st.session_state.page == "Dashboard":
    st.title("Dashboard")
    st.write("You are now on Dashboard page.")


