import streamlit as st
from data.data_read import insert_model_response
from datetime import datetime
from data.data_s3 import download_file, process_data_and_generate_url, RETRIEVAL_EXT, CI_EXT, IMG_EXT, MP3_EXT
import json
from data.data_read import fetch_data_from_db, fetch_data_from_db_dashboards

# Handle file processing and download
def handle_file_processing(question_selected):
    """Process and download the associated file for the selected question."""
    file_name = process_data_and_generate_url(question_selected)
    if file_name == 1:
        st.write('**No file is associated with this question**')
        return None
    else:
        loaded_file = download_file(file_name)
        st.write('Download file:', file_name)
        return loaded_file

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()

question_selected = st.selectbox(
        "**Select a Question:**", 
        options=list(st.session_state.data_frame['Question']),
        index=None,
        key="question_selector",
    )

if question_selected:
        st.text_area("**Selected Question**:", question_selected)
        validate_answer = st.session_state.data_frame[st.session_state.data_frame['Question'] == question_selected]
        task_id_sel = validate_answer['task_id'].iloc[0]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.write('Selected Question Answer is:', validate_answer)

        print(type(question_selected))

        loaded_file = handle_file_processing(question_selected)