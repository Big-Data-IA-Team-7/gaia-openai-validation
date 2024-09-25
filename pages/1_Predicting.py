import streamlit as st
import re
from data.data_read import insert_model_response
from datetime import datetime
from data.data_s3 import download_file, process_data_and_generate_url, RETRIEVAL_EXT, CI_EXT, IMG_EXT, MP3_EXT, ERR_EXT
import json
from data.data_read import fetch_data_from_db
from openai_api.openai_api_call import OpenAIClient
from project_logging import logging_module

logging_module.log_success("Predicting Page")

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAIClient()
if "ask_gpt_clicked" not in st.session_state:
    st.session_state.ask_gpt_clicked = False
if "ask_again_button_clicked" not in st.session_state:
    st.session_state.ask_again_button_clicked = False

with st.sidebar:
    level_filter = st.selectbox("**Difficulty Level**",
                                sorted(st.session_state.data_frame['Level'].unique()),
                                index=None,
    )
    
    file_extensions = ['PDF', 'DOCX', 'TXT', 'PPTX', 'CSV', 'XLSX', 'PY', 'ZIP', 'JPG', 'PNG', 'PDB', 'JSONLD', 'MP3']
    
    extension_filter = st.selectbox("**Extension**",
                                    file_extensions,
                                    index=None,
    )

@st.fragment
def download_fragment(file_name):
    """Fragment containing the download button to avoid full app rerun."""
    st.download_button('Download file', file_name, file_name=file_name, key="download_file_button")

@st.fragment
def gpt_steps(question, answer, model, file):
    steps_on = st.toggle("**Provide Steps**")
    if steps_on:
        handle_wrong_answer_flow(st.session_state.data_frame, question, st.session_state.openai_client, answer, model, file)

# Handle file processing and download
def handle_file_processing(question_selected):
    """Process and download the associated file for the selected question."""
    file_name = process_data_and_generate_url(question_selected)
    if file_name == 1:
        st.write('**No file is associated with this question**')
        return None
    else:
        loaded_file = download_file(file_name)
        download_fragment(loaded_file["path"])
        return loaded_file

def ask_gpt(openai_client, system_content, question_selected, format_type, model, loaded_file=None, annotated_steps=None):
    """Ask GPT for a response and store it in the session state."""
    if format_type == 0:
        validation_content = openai_client.format_content(format_type, question_selected)
    elif format_type == 3:
        validation_content = openai_client.format_content(format_type, question_selected, None, annotated_steps)
    if loaded_file:
        # print(loaded_file)
        if loaded_file["extension"] in RETRIEVAL_EXT:
            ai_response = openai_client.file_validation_prompt(loaded_file["path"], system_content, validation_content, model)
        elif loaded_file["extension"] in CI_EXT:
            ai_response = openai_client.ci_file_validation_prompt(loaded_file["path"], system_content, validation_content, model)
        elif loaded_file["extension"] in IMG_EXT:
            ai_response = openai_client.validation_prompt(system_content, validation_content, model, loaded_file["url"])
        elif loaded_file["extension"] in ERR_EXT:
            ai_response = "The LLM model currently does not support these file extensions."
        else:
            transcription = openai_client.stt_validation_prompt(loaded_file["path"])
            if format_type == 1:
                validation_content = openai_client.format_content(format_type, question_selected, transcription)
            elif format_type == 2:
                validation_content = openai_client.format_content(format_type, question_selected, transcription, annotated_steps)
            ai_response = openai_client.validation_prompt(system_content, validation_content, model)

    else:
        # print(validation_content)
        ai_response = openai_client.validation_prompt(system_content, validation_content, model)
    
    st.session_state.ai_response = ai_response
    
    return ai_response

# Show next steps or handle wrong predictions
def handle_wrong_answer_flow(data_frame, question_selected, openai_client, validate_answer, model, loaded_file=None):
    """Handle wrong answers by showing next steps or allowing GPT to be asked again."""
    steps = data_frame[data_frame['Question'] == question_selected]
    steps = steps['Annotator Metadata'].iloc[0]
    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    st.session_state.steps_text = st.text_area('**Steps:**', steps_text)

    if st.button("Ask GPT Again"):
        if loaded_file and loaded_file["extension"] in MP3_EXT:
            ann_ai_response = ask_gpt(openai_client, openai_client.ann_audio_system_content, 
                                question_selected, 2, model, loaded_file, st.session_state.steps_text)
        else:
            ann_ai_response = ask_gpt(openai_client, openai_client.ann_system_content, 
                                question_selected, 3, model, loaded_file, st.session_state.steps_text)
        
        "**LLM Response**: " + ann_ai_response

        if  answer_validation_check(validate_answer,ann_ai_response):
            st.error("Sorry! GPT predicted the wrong answer even after providing steps.")
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), model, ann_ai_response, 'wrong answer')
        else:
            st.success('GPT predicted the correct answer after the steps were provided.')
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), model, ann_ai_response, 'correct after steps')

def button_click(button):
     st.session_state[button] = True

def button_reset(button):
    st.session_state[button] = False

def answer_validation_check(final_answer,validation_answer):
    final_answer = final_answer.strip().lower()
    validation_answer = validation_answer.strip().lower()

        # Check if final_answer consists only of numbers
    if final_answer.isdigit():
        # Convert validation_answer to a list of elements split by whitespace
        validation_list = validation_answer.split()
        
        # Check if final_answer exists in the validation_list
        return final_answer not in validation_list
    else:
        # If final_answer is not only numbers, perform the original check
        return final_answer not in validation_answer

def filter_questions(level_filter: str = None, extension_filter: str = None):
    # Filtering based on conditions
    if level_filter and extension_filter:
        filtered_questions = st.session_state.data_frame[
            (st.session_state.data_frame['Level'] == level_filter) &
            (st.session_state.data_frame['file_extension'] == extension_filter.lower())
        ]['Question']
    elif level_filter:
        filtered_questions = st.session_state.data_frame[
            st.session_state.data_frame['Level'] == level_filter
        ]['Question']
    elif extension_filter:
        filtered_questions = st.session_state.data_frame[
            st.session_state.data_frame['file_extension'] == extension_filter.lower()
        ]['Question']
    else:
        filtered_questions = st.session_state.data_frame['Question']
    
    return filtered_questions

question_selected = st.selectbox(
        "**Select a Question:**", 
        options=filter_questions(level_filter, extension_filter) ,
        index=None,
    )

model_options = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]

if question_selected:
        st.text_area("**Selected Question**:", question_selected)
        validate_answer = st.session_state.data_frame[st.session_state.data_frame['Question'] == question_selected]
        task_id_sel = validate_answer['task_id'].iloc[0]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.text_input("**Selected Question Answer is:**", validate_answer)

        st.session_state.task_id_sel = task_id_sel

        loaded_file = handle_file_processing(question_selected)

        col1, col2 = st.columns(2)

        model_chosen = col1.selectbox("**Model**",
                                      options=model_options,
                                      index=None,
                                      label_visibility="collapsed"
        )

        gpt_button_clicked = col2.button("Ask GPT", key="gpt_button", on_click=button_click, args=("ask_gpt_clicked",))

        if gpt_button_clicked:
            if not model_chosen:
                button_reset(st.session_state.gpt_button)
                st.error("Please choose a model")
            else:  
                if loaded_file and loaded_file["extension"] in MP3_EXT:
                    system_content = st.session_state.openai_client.audio_system_content
                    format_type = 1
                else:
                    system_content = st.session_state.openai_client.val_system_content
                    format_type = 0
                ai_response = ask_gpt(st.session_state.openai_client, system_content, question_selected, format_type, model_chosen, loaded_file)

                if re.match(r"Error-BDIA", ai_response):
                    st.error("GPT 4 does not work for file search")
                    button_reset(st.session_state.gpt_button)

                elif ai_response== "The LLM model currently does not support these file extensions.":
                    "**LLM Response:** " + ai_response
                    button_reset(st.session_state.gpt_button)

                else: 
                    "**LLM Response:** " + ai_response

                    if  answer_validation_check(validate_answer,ai_response):
                        st.error("Sorry, GPT predicted the wrong answer. Do you need the steps?")
                        gpt_steps(question_selected, validate_answer, model_chosen, loaded_file)
                    else:
                        st.success("GPT predicted the correct answer.")
                        insert_model_response(task_id_sel, datetime.now().date(), model_chosen, ai_response, 'correct as-is')