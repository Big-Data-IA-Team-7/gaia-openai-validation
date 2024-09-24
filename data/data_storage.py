import os
from datasets import load_dataset
from huggingface_hub import login
import json
import boto3
import requests
from mysql.connector import Error
from sqlalchemy import create_engine, text
from datetime import datetime
from db_connection import get_db_connection
from dotenv import load_dotenv
load_dotenv()

# Getting in Environmental variables
hugging_face_token = os.getenv('HUGGINGFACE_TOKEN')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
aws_rds_host=os.getenv('AWS_RDS_HOST')
aws_rds_user=os.getenv('AWS_RDS_USERNAME')
aws_rds_password=os.getenv('AWS_RDS_PASSWORD')
aws_rds_port =os.getenv('AWS_RDS_DB_PORT')
aws_rds_database = os.getenv('AWS_RDS_DATABASE')


# Creating an engine for connecting to the AWS RDS - MySQL database
connection_string = f'mysql+mysqlconnector://{aws_rds_user}:{aws_rds_password}@{aws_rds_host}:{aws_rds_port}'
engine = create_engine(connection_string)



# Login with the token
login(token=hugging_face_token)

# Load the GAIA dataset (including the train split)
ds = load_dataset("gaia-benchmark/GAIA", "2023_all")

# Convert the 'train' split into a pandas DataFrame
train_df = ds['validation'].to_pandas()

#to handle dictionary value for ANNOTATOR METADATA
train_df['Annotator Metadata'] = train_df['Annotator Metadata'].apply(json.dumps)


train_df.to_sql(schema = 'bdia_team7_db',name='gaia_metadata_tbl', con=engine, if_exists='replace', index=False)
print("GAIA dataset loaded into AWS RDS - bdia_team7_db successfully.")

# SQL query to alter the table and add new columns s3 url and file extension
alter_table_query = """
ALTER TABLE bdia_team7_db.gaia_metadata_tbl
ADD COLUMN s3_url varchar(255),
ADD COLUMN file_extension varchar(255);
"""

# Connect to the database and execute the query
with engine.connect() as connection:
    connection.execute(text(alter_table_query))
    print("Column 's3_url and file extension' added successfully.")


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
        select_query = "SELECT * FROM bdia_team7_db.gaia_metadata_tbl WHERE trim(file_name) != ''"
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
                    update_s3url_query = """UPDATE bdia_team7_db.gaia_metadata_tbl
                                      SET s3_url = %s
                                      WHERE task_id = %s"""
                    cursor.execute(update_s3url_query, (s3_url, task_id))
                    connection.commit()
                    print(f"Updated record {task_id} with S3 URL.")


                    # Update the original RDS record with the file extension
                    # SQL query to update the file extension
                    update_file_ext_query = """
                                    UPDATE bdia_team7_db.gaia_metadata_tbl
                                    SET file_extension = SUBSTRING_INDEX(file_name, '.', -1)
                                    WHERE task_id = %s
                                    """

                    # Example Python code to execute the query
                    cursor.execute(update_file_ext_query, (task_id,))
                    connection.commit()
                    print(f"Updated record {task_id} with file extension.")


            except requests.exceptions.RequestException as e:
                print(f"Error downloading {file_name}: {e}")

except Error as e:
    print(f"Error while connecting to MySQL: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
