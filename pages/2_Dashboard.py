# This Python script creates a Streamlit-based dashboard for benchmarking model responses.
# It reads data from a database and sets up an interactive visualization for users to explore.
# The dashboard allows users to filter questions based on their level (e.g., Level 1, 2, 3, or Overall) 
# and select different models to analyze their performance. The script merges data from two tables 
# to display relevant metrics like response categories and model answers, then visualizes this information
# using an Altair bar chart. The 'dashboard_dataframe' function handles displaying the data table and chart 
# for the selected filters.

import streamlit as st
import pandas as pd
from data.data_read import fetch_data_from_db, fetch_data_from_db_dashboards
import altair as alt

st.session_state.data_frame_dashboard = fetch_data_from_db_dashboards()

with st.sidebar:
    selected_level = st.selectbox(
            "**Select a Level:**", 
            ["Overall","Level 1", "Level 2","Level 3"],
            index=None,
            key="level_selector",
        )

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()

def dashboard_dataframe(dataframe: pd.DataFrame) -> None:
    """
    Generates and displays a data table and a bar chart visualization for the given DataFrame
    based on the response categories.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing response categories and their counts.

    Returns:
        None
    """
    overall=dataframe['response_category'].value_counts().reset_index()
    overall['response_category'] = overall['response_category'].str.upper()
    overall.columns = ["Response Category", "Number of Questions"]

    st.dataframe(
        overall,
    hide_index=True)

    bar_chart = alt.Chart(overall).mark_bar(color="#ffd21f", size=40).encode(
        x=alt.X('Response Category:O', axis=alt.Axis(labelAngle=0, labelLimit=200, titleFontWeight='bold')),
        y=alt.Y("Number of Questions:Q", axis=alt.Axis(titleFontWeight='bold'))
        )
    
    st.altair_chart(bar_chart, use_container_width=True)

def model_perf_table(dataframe: pd.DataFrame) -> None:
    st.header("OpenAI Model Performance", divider="gray")

    grouped_df = dataframe.groupby(['model_used', 'Level', 'response_category']).size().unstack(fill_value=0).reset_index()

    grouped_df['total_correct'] = grouped_df['correct after steps'] + grouped_df['correct as-is']
    grouped_df['total_questions'] = grouped_df['correct after steps'] + grouped_df['correct as-is'] + grouped_df['wrong answer']

    # Calculate the score for each level
    grouped_df['level_score'] = (grouped_df['total_correct'] / grouped_df['total_questions']) * 100

    # Calculate the average score across all levels for each model
    average_scores_df = grouped_df.groupby('model_used').agg(
        average_score=('level_score', 'mean'),
        level_1_score=('level_score', lambda x: x[grouped_df['Level'] == '1'].mean() if '1' in grouped_df['Level'].values else 0),
        level_2_score=('level_score', lambda x: x[grouped_df['Level'] == '2'].mean() if '2' in grouped_df['Level'].values else 0),
        level_3_score=('level_score', lambda x: x[grouped_df['Level'] == '3'].mean() if '3' in grouped_df['Level'].values else 0)
    ).reset_index()

    st.dataframe(
        average_scores_df,
        hide_index=True,
            column_config={
        "model_used": "Model",
        "average_score": "Average Score (%)",
        "level_1_score": "Level 1 Score (%)",
        "level_2_score": "Level 2 Score (%)",
        "level_3_score": "Level 3 Score (%)",
    })

st.title("Dashboard")

#Joining 2 table to the validate answer 
merger_df=pd.merge(st.session_state.data_frame,st.session_state.data_frame_dashboard,on='task_id',how='inner')
merger_df=merger_df[['task_id','Level','Final answer','model_used','model_response','response_category']]

model_perf_table(merger_df)
    
if selected_level:
    st.header(f"Benchmarking on {selected_level} questions", divider="gray")
    
    # Determine if we're using 'Overall' or a specific level
    if selected_level == 'Overall':
        filtered_df = merger_df
    else:
        level_number = selected_level.split()[-1]
        filtered_df = merger_df[merger_df['Level'] == level_number]

    # Get unique models for the selectbox
    model_value = filtered_df['model_used'].unique()
    
    selected_model = st.selectbox(
        "**Select a Model:**", 
        options=model_value,
        index=None
    )

    if selected_model:
        st.header(f"{selected_model} Performance", divider="gray")
        # Filter based on the selected model
        model_selection = filtered_df[filtered_df['model_used'] == selected_model]
        
        # Display the relevant DataFrame using your function
        dashboard_dataframe(model_selection)