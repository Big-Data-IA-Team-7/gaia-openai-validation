# This Python script sets up a Streamlit interface for generating predictions using the OpenAI API.
# It initializes session state variables for data retrieval, interacts with a database to fetch data, and manages
# user inputs through a sidebar for filtering by difficulty level. The script also handles interactions with the OpenAI 
# client for generating model responses and logs actions to monitor the usage of this prediction page.

import streamlit as st
import re
import json
from datetime import datetime
from data.data_s3 import download_file, process_data_and_generate_url, MP3_EXT
from data.data_read import fetch_data_from_db
from data.data_read import insert_model_response
from openai_api.openai_api_call import OpenAIClient
from openai_api.openai_api_streamlit import ask_gpt, answer_validation_check

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
def download_fragment(file_name: str) -> None:
    """
    A Streamlit fragment that displays a download button for the specified file.

    Args:
        file_name (str): The name of the file to be made available for download.

    Returns:
        None
    """
    st.download_button('Download file', file_name, file_name=file_name, key="download_file_button")

@st.fragment
def gpt_steps(question: str, answer: str, model: str, file: dict) -> None:
    """
    Displays a toggle to provide steps and handles the wrong answer flow if activated.

    Args:
        question (str): The selected question.
        answer (str): The provided answer.
        model (str): The model used for generating responses.
        file (dict): The file details for handling file-based prompts.

    Returns:
        None
    """
    steps_on = st.toggle("**Provide Steps**")
    if steps_on:
        handle_wrong_answer_flow(st.session_state.data_frame, question, st.session_state.openai_client, answer, model, file)

def handle_file_processing(question_selected: str, dataframe) -> dict:
    """
    Processes the associated file for the selected question and provides a download option.

    Args:
        question_selected (str): The question for which the associated file needs to be processed.
        dataframe (pd.DataFrame): The DataFrame containing data for the selected question.

    Returns:
        dict: A dictionary containing the details of the downloaded file if successful.
        None: Returns None if no file is associated with the selected question.
    """
    file_name = process_data_and_generate_url(question_selected, dataframe)
    if file_name == "1":
        st.write('**No file is associated with this question**')
        return None
    else:
        loaded_file = download_file(file_name)
        download_fragment(loaded_file["path"])
        return loaded_file

@st.fragment
def handle_wrong_answer_flow(data_frame, question_selected: str, openai_client, validate_answer: str, model: str, loaded_file: dict = None) -> None:
    """
    Handles the flow for handling wrong answers by displaying next steps and allowing the option to ask GPT again.

    Args:
        data_frame (pd.DataFrame): The DataFrame containing questions and their associated metadata.
        question_selected (str): The question for which the answer is being validated.
        openai_client (OpenAIClient): The client instance used to interact with the OpenAI API.
        validate_answer (str): The correct answer against which the GPT's response will be validated.
        model (str): The model to be used for generating the response (e.g., "gpt-4").
        loaded_file (dict, optional): The file details dictionary containing 'path' and 'extension' for handling file-based prompts. Defaults to None.

    Returns:
        None: This function does not return a value; it handles the logic of displaying results and updating session state.
    """
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

def button_click(button: str) -> None:
    """
    Sets the specified button's state to True in the Streamlit session state.

    Args:
        button (str): The key representing the button in the session state.

    Returns:
        None
    """
    st.session_state[button] = True

def button_reset(button: str) -> None:
    """
    Resets the specified button's state to False in the Streamlit session state.

    Args:
        button (str): The key representing the button in the session state.

    Returns:
        None
    """
    st.session_state[button] = False

def filter_questions(level_filter: str = None, extension_filter: str = None):
    """
    Filters questions from the session state DataFrame based on the specified level and/or file extension.

    Args:
        level_filter (str, optional): The level to filter questions by. Defaults to None.
        extension_filter (str, optional): The file extension to filter questions by. Defaults to None.

    Returns:
        pd.Series: A pandas Series containing the filtered questions.
    """
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

model_options = ["GPT-4o", "GPT-4", "GPT-3.5-turbo"]

if question_selected:
        st.text_area("**Selected Question**:", question_selected)
        validate_answer = st.session_state.data_frame[st.session_state.data_frame['Question'] == question_selected]
        task_id_sel = validate_answer['task_id'].iloc[0]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.text_input("**Selected Question Answer is:**", validate_answer)

        st.session_state.task_id_sel = task_id_sel

        loaded_file = handle_file_processing(question_selected, st.session_state.data_frame)

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

                if ai_response:
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