import os
from datasets import load_dataset
from huggingface_hub import login
import json
import mysql.connector
import boto3
import requests
from mysql.connector import Error
from sqlalchemy import create_engine, text
from datetime import datetime

# Getting in Environmental variables
hugging_face_token = os.getenv('HUGGINGFACE_TOKEN')
aws_rds_host=os.getenv('AWS_RDS_HOST')
aws_rds_user=os.getenv('AWS_RDS_USERNAME')
aws_rds_password=os.getenv('AWS_RDS_PASSWORD')
aws_rds_port =os.getenv('AWS_RDS_DB_PORT')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
aws_rds_database = os.getenv('AWS_RDS_DATABASE')

# Creating an engine for connecting to the AWS RDS - MySQL database
connection_string = f'mysql+mysqlconnector://{aws_rds_user}:{aws_rds_password}@{aws_rds_host}:{aws_rds_port}'
engine = create_engine(connection_string)

def get_db_connection():
    return mysql.connector.connect(
        host= aws_rds_host,
        user=aws_rds_user,
        password=aws_rds_password,
        port =aws_rds_port,
        database=aws_rds_database
    )

# Login with the token
login(token=hugging_face_token)

# Load the GAIA dataset (including the train split)
ds = load_dataset("gaia-benchmark/GAIA", "2023_all")

# Convert the 'train' split into a pandas DataFrame
train_df = ds['validation'].to_pandas()

#to handle dictionary value for ANNOTATOR METADATA
train_df['Annotator Metadata'] = train_df['Annotator Metadata'].apply(json.dumps)


train_df.to_sql(schema = 'bdia_team7_db',name='gaia_metadata_tbl_test', con=engine, if_exists='replace', index=False)
print("GAIA dataset loaded into AWS RDS - bdia_team7_db successfully.")

# SQL query to alter the table and add a new column
alter_table_query = """
ALTER TABLE bdia_team7_db.gaia_metadata_tbl_test 
ADD COLUMN s3_url varchar(255);
"""

# Connect to the database and execute the query
with engine.connect() as connection:
    connection.execute(text(alter_table_query))
    print("Column 's3_url' added successfully.")


# AWS S3 setup
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


# Hugging Face base URL for validation files
huggingface_base_url = 'https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation/'

# Step 1: Connect to MySQL RDS and fetch records where file_name is not null
try:
    # MySQL RDS connection
    connection = get_db_connection()

    headers = {
        "Authorization": f"Bearer {hugging_face_token}"
        }

    if connection.is_connected():
        cursor = connection.cursor(dictionary=True)

        # Fetch records where file_name is not null
        select_query = "SELECT * FROM bdia_team7_db.gaia_metadata_tbl_test WHERE trim(file_name) != ''"
        cursor.execute(select_query)
        records = cursor.fetchall()

        for record in records:
            task_id = record['task_id']
            file_name = record['file_name'].strip()

            # Download file from Hugging Face
            file_url = huggingface_base_url + file_name
            print(file_url)
            try:
                response = requests.get(file_url, headers=headers)
                print(response.status_code)
                if response.status_code == 200:
                    file_data = response.content
                    print(f"Downloaded {file_name} from Hugging Face.")

                    # Upload the file to S3
                    s3_key = f"gaia_files/{file_name}"
                    #s3.put_object(Bucket=aws_bucket_name, Key=s3_key, Body=file_data)
                    s3_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{s3_key}"
                    print(f"Uploaded {file_name} to S3 at {s3_url}")

                    # Update the original RDS record with the S3 URL
                    update_query = """UPDATE bdia_team7_db.gaia_metadata_tbl_test
                                      SET s3_url = %s
                                      WHERE task_id = %s"""
                    cursor.execute(update_query, (s3_url, task_id))
                    connection.commit()
                    print(f"Updated record {task_id} with S3 URL.")

            except requests.exceptions.RequestException as e:
                print(f"Error downloading {file_name}: {e}")

except Error as e:
    print(f"Error while connecting to MySQL: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")



# Function to insert a model's response into the database
def insert_model_response(task_id, date, model_used, model_response, response_category, created_at=datetime.now(), created_by='streamlit user'):
    """
    Inserts a new record into the 'model_response' table.

    Parameters:
        task_id (str): The unique identifier for the task.
        date (str): The date when the task was created or processed (format: 'YYYY-MM-DD').
        model_used (str): The model used to generate the response (e.g., GPT-4).
        model_response (str): The response generated by the model.
        response_category (str): The category or type of the response.
        created_at (datetime, optional): The timestamp when the record is created. Defaults to the current datetime.
        created_by (str, optional): The user/system creating the record. Defaults to 'system'.
    
    Returns:
        None
    
    Raises:
        Error: Catches and prints any MySQL connection or query execution errors.
    
    Notes:
        - This function connects to the MySQL database, executes an INSERT query, and commits the transaction.
        - The database connection is closed after execution to prevent resource leaks.
    """
    try:
        # Establish connection to the MySQL database
        connection = get_db_connection()

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # SQL INSERT query to add a new row to the 'model_response' table
        insert_query = """
        INSERT INTO model_response (task_id, date, model_used, model_response, response_category, created_at, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # Execute the query with the provided parameters
        cursor.execute(insert_query, (task_id, date, model_used, model_response, response_category, created_at, created_by))

        # Commit the transaction to save the changes to the database
        connection.commit()

    except Error as e:
        # Print the error message in case of a MySQL connection or execution error
        print(f"Error while connecting to MySQL: {e}")

    finally:
        # Ensure that the cursor and the connection are closed properly to free up resources
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")
