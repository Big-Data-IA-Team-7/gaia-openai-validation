import streamlit as st
from data.data_read import insert_model_response
from datetime import datetime
from data.data_s3 import download_file, process_data_and_generate_url, RETRIEVAL_EXT, CI_EXT, IMG_EXT, MP3_EXT
import json
from data.data_read import fetch_data_from_db
from openai_api.openai_api_call import OpenAIClient

@st.fragment
def download_fragment(file_name):
    """Fragment containing the download button to avoid full app rerun."""
    st.download_button('Download file', file_name, file_name=file_name, key="download_file_button")

@st.fragment
def gpt_steps(question, answer, file):
    steps_on = st.toggle("**Provide Steps**")
    if steps_on:
        handle_wrong_answer_flow(st.session_state.data_frame, question, st.session_state.openai_client, answer, file)

# Handle file processing and download
def handle_file_processing(question_selected):
    """Process and download the associated file for the selected question."""
    file_name = process_data_and_generate_url(question_selected)
    if file_name == 1:
        st.write('**No file is associated with this question**')
        return None
    else:
        loaded_file = download_file(file_name)
        download_fragment(file_name)
        return loaded_file

def ask_gpt(openai_client, system_content, question_selected, format_type, loaded_file=None, annotated_steps=None):
    """Ask GPT for a response and store it in the session state."""
    if format_type == 3:
        validation_content = openai_client.format_content(format_type, question_selected, None, annotated_steps)
    elif format_type == 0:
        validation_content = openai_client.format_content(format_type, question_selected)
    if loaded_file:
        if loaded_file["extension"] in RETRIEVAL_EXT:
            ai_response = openai_client.file_validation_prompt(loaded_file["path"], system_content, validation_content)
        elif loaded_file["extension"] in CI_EXT:
            ai_response = openai_client.ci_file_validation_prompt(loaded_file["path"], system_content, validation_content)
        elif loaded_file["extension"] in IMG_EXT:
            ai_response = openai_client.image_validation_prompt(loaded_file["url"], system_content, validation_content)
        else:
            transcription = openai_client.stt_validation_prompt(loaded_file["path"], system_content)
            if format_type == 1:
                validation_content = openai_client.format_content(format_type, question_selected, transcription)
            elif format_type == 2:
                validation_content = openai_client.format_content(format_type, question_selected, transcription, annotated_steps)
            ai_response = openai_client.validation_prompt(system_content, validation_content)

    else:
        ai_response = openai_client.validation_prompt(system_content, validation_content)
    
    st.session_state.ai_response = ai_response
    
    return ai_response

# Show next steps or handle wrong predictions
def handle_wrong_answer_flow(data_frame, question_selected, openai_client, validate_answer, loaded_file=None):
    """Handle wrong answers by showing next steps or allowing GPT to be asked again."""
    steps = data_frame[data_frame['Question'] == question_selected]
    steps = steps['Annotator Metadata'].iloc[0]
    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    st.session_state.steps_text = st.text_area('**Steps:**', steps_text)

    if st.button("Ask GPT Again"):
        if loaded_file and loaded_file["extension"] in MP3_EXT:
            ann_ai_response = ask_gpt(openai_client, openai_client.ann_audio_system_content, 
                                question_selected, 2,loaded_file, st.session_state.steps_text)
        else:
            ann_ai_response = ask_gpt(openai_client, openai_client.ann_system_content, 
                                question_selected, 3, loaded_file, st.session_state.steps_text)
        
        "**LLM Response**: " + ann_ai_response

        if ann_ai_response not in validate_answer:
            st.error("Sorry! GPT predicted the wrong answer even after providing steps.")
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'wrong answer')
        else:
            st.success('GPT predicted the correct answer after the steps were provided.')
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'correct after steps')

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAIClient()
if "ask_gpt_clicked" not in st.session_state:
    st.session_state.ask_gpt_clicked = False
if "ask_again_button_clicked" not in st.session_state:
    st.session_state.ask_again_button_clicked = False

def button_click(button):
     st.session_state[button] = True

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
        st.text_input("**Selected Question Answer is:**", validate_answer)

        st.session_state.task_id_sel = task_id_sel

        loaded_file = handle_file_processing(question_selected)

        gpt_button_clicked = st.button("Ask GPT", on_click=button_click, args=("ask_gpt_clicked",))
        if gpt_button_clicked:
            if loaded_file and loaded_file["extension"] in MP3_EXT:
                    system_content = st.session_state.openai_client.audio_system_content
                    format_type = 1
            else:
                system_content = st.session_state.openai_client.val_system_content
                format_type = 0
            ai_response = ask_gpt(st.session_state.openai_client, system_content, question_selected, format_type, loaded_file)

            "**LLM Response:** " + ai_response

            if ai_response not in validate_answer:
                st.error("Sorry, GPT predicted the wrong answer. Do you need the steps?")
                gpt_steps(question_selected, validate_answer, loaded_file)
