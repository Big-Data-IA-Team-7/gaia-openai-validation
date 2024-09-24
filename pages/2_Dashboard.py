import streamlit as st
import pandas as pd
from data.data_read import fetch_data_from_db, fetch_data_from_db_dashboards


from project_logging import logging_module

logging_module.log_success("Dashboard Page")

st.session_state.data_frame_dashboard = fetch_data_from_db_dashboards()

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()

st.title("Dashboard")

#Joining 2 table to the validate answer 
merger_df=pd.merge(st.session_state.data_frame,st.session_state.data_frame_dashboard,on='task_id',how='inner')
merger_df=merger_df[['task_id','Level','Final answer','model_used','model_response','response_category']]

 # Select Box for Dashboards
with st.sidebar:
    dash_selection = st.selectbox(
            "**Select a Level:**", 
            ["Overall","Level 1", "Level 2","Level 3"],
            index=None,
            key="question_selector",
        )
    
if dash_selection:
    st.write(f'Dashboard based on {dash_selection} Selection')
    
# st.dataframe(merger_df)

# Filter Model 
if dash_selection:
    if dash_selection == 'Overall':
        # Use the 'count' dataframe for 'Overall' selection
        model_value=merger_df['model_used'].unique()
    else:
        # Extract the level number from 'Level X' (e.g., 'Level 1' => '1')
        level_number = dash_selection.split()[-1]
        model_value=merger_df[merger_df['Level']==level_number]
        model_value=model_value['model_used'].unique()
    Selecting_model = st.selectbox(
            "**Select a Model:**", 
            options=  model_value,
            index=None,
        )   

# Handle all selections with a single if
if dash_selection in ['Overall', 'Level 1', 'Level 2', 'Level 3']:
    if dash_selection == 'Overall':
        if Selecting_model:
            # Use the 'count' dataframe for 'Overall' selection
            model_selection_overall=merger_df[merger_df['model_used']==Selecting_model]
            overall=model_selection_overall['response_category'].value_counts().reset_index()
            overall.columns=['response_category','count']
            st.dataframe(overall)
            st.bar_chart(overall.set_index('response_category')['count'],use_container_width=False,width=150)
    else:
        # Count the occurrences of response_category and Level
        level_wise_count = merger_df.groupby(['response_category', 'Level']).size().reset_index(name='count')
        if Selecting_model:
            model_selection_overall=merger_df[merger_df['model_used']==Selecting_model]
            # Extract the level number from 'Level X' (e.g., 'Level 1' => '1')
            level_number = dash_selection.split()[-1]
            level_wise_count=merger_df[merger_df['model_used']==Selecting_model]
            level_wise_count=level_wise_count[level_wise_count['Level'] == level_number]
            overall=level_wise_count['response_category'].value_counts().reset_index()
            overall.columns=['response_category','count']
            st.dataframe(overall)
            st.bar_chart(overall.set_index('response_category')['count'],use_container_width=False,width=150)