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
merger_df=merger_df[['task_id','Final answer','model_response','response_category']]
st.dataframe(merger_df)
count=merger_df['response_category'].value_counts()


# Create a Matplotlib figure
fig, ax = plt.subplots()
ax.bar(count.index, count.values)

# Add labels and title
ax.set_xlabel('Response Category')
ax.set_ylabel('Count')
ax.set_title('Response Category Distribution')

# Display the bar graph in Streamlit
st.pyplot(fig)