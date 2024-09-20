import streamlit as st
from data.data_storage import insert_model_response
from datetime import datetime
from data.data_s3 import download_file
from data.data_s3 import process_data_and_generate_url
import json

# Reset session state for the button interaction
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

# Render selectbox for question selection
def render_question_selector(data_frame):
    """Render a selectbox for selecting questions."""
    placeholder_text = "Select a Question"
    question_selected = st.selectbox(
        'Select a Question', 
        options=[placeholder_text] + list(data_frame['Question']),
        index=0
    )
    if question_selected != st.session_state.previous_question:
        reset_interaction_state()
        st.session_state.previous_question = question_selected
    return question_selected

# Handle file processing and download
def handle_file_processing(question_selected):
    """Process and download the associated file for the selected question."""
    file_name = process_data_and_generate_url(question_selected)
    if file_name == 1:
        st.write('No file is associated with this question')
        return None
    else:
        file_path = download_file(file_name)
        st.write('Download file:', file_name)
        return file_path

# Ask GPT and handle AI responses
def ask_gpt(openai_client, question_selected, validate_answer, file_path=None):
    """Ask GPT for a response and store it in the session state."""
    validation_content = openai_client.format_content(0, question_selected)
    if file_path:
        ai_response = openai_client.file_validation_prompt(file_path, openai_client.val_system_content, validation_content)
    else:
        ai_response = openai_client.validation_prompt(openai_client.val_system_content, validation_content)
    st.session_state.ai_response = ai_response
    return ai_response

# Show next steps or handle wrong predictions
def handle_wrong_answer_flow(data_frame, question_selected, openai_client, validate_answer, file_path=None):
    """Handle wrong answers by showing next steps or allowing GPT to be asked again."""
    steps = data_frame[data_frame['Question'] == question_selected]
    steps = steps['Annotator Metadata'].iloc[0]
    steps_dict = json.loads(steps)
    steps_text = steps_dict.get('Steps', 'No steps found')

    st.session_state.steps_text = st.text_area('Steps:', steps_text)

    if st.button("Ask GPT Again"):
        ann_validation_content = openai_client.format_content(1, question_selected, st.session_state.steps_text)
        if file_path:
            ann_ai_response = openai_client.file_validation_prompt(file_path, openai_client.ann_system_content, ann_validation_content)
        else:
            ann_ai_response = openai_client.validation_prompt(openai_client.ann_system_content, ann_validation_content)

        st.write(ann_ai_response)

        if ann_ai_response not in validate_answer:
            st.error("Sorry! GPT still predicted the wrong answer after providing steps.")
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'wrong answer')
        else:
            st.success('GPT predicted the correct answer after the steps were provided.')
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'correct after steps')

# Main rendering function
def render_predicting_page(data_frame, openai_client):
    """Render the Predicting page content."""
    question_selected = render_question_selector(data_frame)
    
    if question_selected != "Select a Question":
        st.text_area("Selected Question:", question_selected)
        validate_answer = data_frame[data_frame['Question'] == question_selected]
        task_id_sel = validate_answer['task_id'].iloc[0]
        validate_answer = validate_answer['Final answer'].iloc[0]
        st.write('Selected Question Answer is:', validate_answer)

        st.session_state.task_id_sel = task_id_sel

        file_path = handle_file_processing(question_selected)

        if not st.session_state.ask_gpt_clicked:
            if st.button('Ask GPT'):
                st.session_state.ask_gpt_clicked = True
                ai_response = ask_gpt(openai_client, question_selected, validate_answer, file_path)

                if ai_response not in validate_answer:
                    st.session_state.show_next_steps = False
                    st.session_state.show_no_response = False
                else:
                    st.success("GPT predicted the correct answer.")
                    insert_model_response(task_id_sel, datetime.now().date(), 'gpt-4o', ai_response, 'correct as-is')

        if st.session_state.ask_gpt_clicked:
            ai_response = st.session_state.ai_response
            st.write(ai_response)

            if ai_response not in validate_answer:
                st.error("Sorry, GPT predicted the wrong answer. Do you need the steps?")
                
                if not st.session_state.show_next_steps and not st.session_state.show_no_response:
                    col1, col2 = st.columns(2)
                    with col1:
                        if not st.session_state.show_no_response:
                            if st.button("Yes"):
                                st.session_state.show_next_steps = True
                                st.session_state.show_no_response = False
                                st.session_state.show_reset_button = False
                                st.session_state.show_ask_gpt_again = True
                    with col2:
                        if not st.session_state.show_next_steps:
                            if st.button('No'):
                                reset_interaction_state()
                                st.experimental_rerun()

                if st.session_state.show_next_steps:
                    handle_wrong_answer_flow(data_frame, question_selected, openai_client, validate_answer, file_path)
    else:
        st.write("Please select a valid question to proceed.")
