import streamlit as st
from data.data_read import insert_model_response
from datetime import datetime
from data.data_s3 import download_file, process_data_and_generate_url, RETRIEVAL_EXT, CI_EXT, IMG_EXT, MP3_EXT
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
        loaded_file = download_file(file_name)
        st.write('Download file:', file_name)
        return loaded_file

# Ask GPT and handle AI responses
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

    st.session_state.steps_text = st.text_area('Steps:', steps_text)

    if st.button("Ask GPT Again"):
        if loaded_file:
            if loaded_file["extension"] in MP3_EXT:
                ann_ai_response = ask_gpt(openai_client, openai_client.ann_audio_system_content, 
                                    question_selected, 2,loaded_file, st.session_state.steps_text)
            else:
                ann_ai_response = ask_gpt(openai_client, openai_client.ann_system_content, 
                                question_selected, 3, loaded_file, st.session_state.steps_text)
        else:
            ann_ai_response = ask_gpt(openai_client, openai_client.ann_system_content, 
                                question_selected, 3, loaded_file, st.session_state.steps_text)
        st.write(ann_ai_response)

        if ann_ai_response not in validate_answer:
            st.error("Sorry! GPT still predicted the wrong answer after providing steps.")
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'wrong answer')
        else:
            st.success('GPT predicted the correct answer after the steps were provided.')
            insert_model_response(st.session_state.task_id_sel, datetime.now().date(), 'gpt-4o', ann_ai_response, 'correct after steps')

# Main rendering function
def render_predicting_page(data_frame, openai_client):
    """Render the Predicting page content with selectboxes next to each other."""
    
    # Initially show a placeholder value
    placeholder_text = "Select a Question"
    filter_text = "Select Level"
    filter_data = sorted(data_frame['Level'].unique())

    # Create two columns for the select boxes
    col1, col2 = st.columns(2)  # Two equal-width columns
    
    with col1:
        filter_selected = st.selectbox(
            'Select Level for the Question',
            options=[filter_text] + filter_data,
            index=0,
            format_func=lambda x: f"{x}",  # Format function to adjust display
            key='level_select',  # Unique key for the selectbox
            help='Choose the level for the question',
        )
        # Reduce the width of the selectbox using markdown
        st.markdown("<style>div[role='listbox'] { max-width: 100px; }</style>", unsafe_allow_html=True)  # Adjust the max-width as needed
    
    with col2:
        filter_selected_question = data_frame[data_frame['Level'] == filter_selected]['Question']
        
        # Selectbox for the question, default is the placeholder
        question_selected = st.selectbox(
            'Select a Question', 
            options=[placeholder_text] + list(filter_selected_question),  # Adding placeholder to the list of questions
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
        validate_answer = data_frame[data_frame['Question'] == question_selected]['Final answer'].iloc[0]
        st.write('Selected Question Answer is:', validate_answer)
        file_name = process_data_and_generate_url(question_selected)
        if file_name == 1:
            st.write('No file is associated with this question')
        else:
            file_path = download_file(file_name)
            st.write('Download file:', file_name)
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
                    steps = data_frame[data_frame['Question'] == question_selected]['Annotator Metadata'].iloc[0]
                    steps_dict = json.loads(steps)
                    steps_text = steps_dict.get('Steps', 'No steps found')
                    steps_question = st.text_area('Steps:', steps_text)
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
                            print('validate_answer', validate_answer)
                            st.error("Sorry!!! GPT Unable to predict the correct Answer after the steps provided")
                        else:
                            print('validate_answer', validate_answer)
                            st.success('GPT Predicted the correct Answer')
    else:
        st.write("Please select a valid question to proceed.")
