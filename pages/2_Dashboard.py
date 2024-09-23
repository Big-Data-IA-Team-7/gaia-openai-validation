import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data.data_read import fetch_data_from_db, fetch_data_from_db_dashboards

# Initialize session state for the data
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = fetch_data_from_db()
if 'data_frame_dashboard' not in st.session_state:
    st.session_state.data_frame_dashboard = fetch_data_from_db_dashboards()

st.title("Dashboard")
st.write("You are now on Dashboard page.")
#Joining 2 table to the validate answer 
merger_df=pd.merge(st.session_state.data_frame,st.session_state.data_frame_dashboard,on='task_id',how='inner')
merger_df=merger_df[['task_id','Level','Final answer','model_response','response_category']]
# st.dataframe(merger_df)
count=merger_df['response_category'].value_counts().reset_index()
count.columns=['response_category','count']

# Select Box for Dashboards
dash_selection = st.selectbox(
        "**Select a Level:**", 
        ["Overall","Level 1", "Level 2","Level 3"],
        index=None,
        key="question_selector",
    )

# Count the occurrences of response_category and Level
level_wise_count = merger_df.groupby(['response_category', 'Level']).size().reset_index(name='count')

# st.write('Overall Counting')
# st.dataframe(level_wise_count)



#Overall count bar Graph
if dash_selection=='Overall':
    st.dataframe(count)    
    st.bar_chart(count.set_index('response_category')['count'])

#Level 1 count bar Graph
if dash_selection=='Level 1':
    level_wise_count_level=level_wise_count[level_wise_count['Level']=='1']
    st.dataframe(level_wise_count_level)
    st.bar_chart(level_wise_count_level.set_index('response_category')['count'],use_container_width=False,width=100)
    

if dash_selection=='Level 2':
    level_wise_count_level=level_wise_count[level_wise_count['Level']=='2']
    st.dataframe(level_wise_count_level)
    st.bar_chart(level_wise_count_level.set_index('response_category')['count'])

if dash_selection=='Level 3':
    level_wise_count_level=level_wise_count[level_wise_count['Level']=='3']
    st.dataframe(level_wise_count_level)
    st.bar_chart(level_wise_count_level.set_index('response_category')['count'])


# # Create a Matplotlib figure
# fig, ax = plt.subplots()
# ax.bar(count.index, count.values)

# # Add labels and title
# ax.set_xlabel('Response Category')
# ax.set_ylabel('Count')
# ax.set_title('Response Category Distribution')

# # Display the bar graph in Streamlit
# st.pyplot(fig)