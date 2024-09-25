import streamlit as st
import pandas as pd
from data.data_read import fetch_data_from_db, fetch_data_from_db_dashboards
import altair as alt

st.session_state.data_frame_dashboard = fetch_data_from_db_dashboards()

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()

def dashboard_dataframe(dataframe):
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

st.title("Dashboard")

#Joining 2 table to the validate answer 
merger_df=pd.merge(st.session_state.data_frame,st.session_state.data_frame_dashboard,on='task_id',how='inner')
merger_df=merger_df[['task_id','Level','Final answer','model_used','model_response','response_category']]

 # Select Box for Dashboards
with st.sidebar:
    selected_level = st.selectbox(
            "**Select a Level:**", 
            ["Overall","Level 1", "Level 2","Level 3"],
            index=None,
            key="level_selector",
        )
    
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