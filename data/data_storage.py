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
import data_storage_log as logging_module

# Load environment variables
load_dotenv()



# Getting environmental variables
hugging_face_token = os.getenv('HUGGINGFACE_TOKEN')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
aws_rds_host = os.getenv('AWS_RDS_HOST')
aws_rds_user = os.getenv('AWS_RDS_USERNAME')
aws_rds_password = os.getenv('AWS_RDS_PASSWORD')
aws_rds_port = os.getenv('AWS_RDS_DB_PORT')
aws_rds_database = os.getenv('AWS_RDS_DATABASE')


# Creating an engine for connecting to the AWS RDS - MySQL database
try:
    connection_string = f'mysql+mysqlconnector://{aws_rds_user}:{aws_rds_password}@{aws_rds_host}:{aws_rds_port}'
    engine = create_engine(connection_string)
    logging_module.log_success("MySQL connection engine created successfully.")
except Exception as e:
    logging_module.log_error(f"Failed to create MySQL connection engine: {e}")

# Login with the Hugging Face token
try:
    login(token=hugging_face_token)
    logging_module.log_success("Logged in to Hugging Face successfully.")
except Exception as e:
    logging_module.log_error(f"Failed to login to Hugging Face: {e}")

# Load the GAIA dataset
try:
    ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
    logging_module.log_success("GAIA dataset loaded successfully.")
except Exception as e:
    logging_module.log_error(f"Error loading GAIA dataset: {e}")

# Convert the 'validation' split into a pandas DataFrame
try:
    train_df = ds['validation'].to_pandas()
    train_df['Annotator Metadata'] = train_df['Annotator Metadata'].apply(json.dumps)
    train_df.to_sql(schema='bdia_team7_db', name='gaia_metadata_tbl', con=engine, if_exists='replace', index=False)
    logging_module.log_success("GAIA dataset loaded into AWS RDS - bdia_team7_db successfully.")
except Exception as e:
    logging_module.log_error(f"Error saving GAIA dataset to MySQL: {e}")

# SQL query to alter the table and add new columns s3_url and file_extension
alter_table_query = """
ALTER TABLE bdia_team7_db.gaia_metadata_tbl
ADD COLUMN s3_url varchar(255),
ADD COLUMN file_extension varchar(255);
"""

# Execute the alter table query
try:
    with engine.connect() as connection:
        connection.execute(text(alter_table_query))
        logging_module.log_success("Columns 's3_url' and 'file_extension' added successfully.")
except Exception as e:
    logging_module.log_error(f"Error altering table to add columns: {e}")

# AWS S3 setup
try:
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    logging_module.log_success("Connected to S3 bucket.")
except Exception as e:
    logging_module.log_error(f"Error connecting to S3: {e}")

# Hugging Face base URL for validation files
huggingface_base_url = 'https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation/'

# Connect to MySQL RDS and fetch records where file_name is not null
try:
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
        logging_module.log_success(f"Fetched records from bdia_team7_db.gaia_metadata_tbl.")

        for record in records:
            task_id = record['task_id']
            file_name = record['file_name'].strip()

            # Download file from Hugging Face
            file_url = huggingface_base_url + file_name
            try:
                response = requests.get(file_url, headers=headers)
                if response.status_code == 200:
                    file_data = response.content
                    logging_module.log_success(f"Downloaded {file_name} from Hugging Face.")

                    # Upload the file to S3
                    s3_key = f"gaia_files/{file_name}"
                    s3.put_object(Bucket=aws_bucket_name, Key=s3_key, Body=file_data)
                    s3_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{s3_key}"
                    logging_module.log_success(f"Uploaded {file_name} to S3 at {s3_url}")

                    # Update the original RDS record with the S3 URL
                    try:
                        update_s3url_query = """UPDATE bdia_team7_db.gaia_metadata_tbl
                                                SET s3_url = %s
                                                WHERE task_id = %s"""
                        cursor.execute(update_s3url_query, (s3_url, task_id))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with S3 URL.")
                    except Exception as e:
                        logging_module.log_error(f"Error updating S3 URL for task_id {task_id}: {e}")

                    # Update the original RDS record with the file extension
                    try:
                        update_file_ext_query = """
                            UPDATE bdia_team7_db.gaia_metadata_tbl
                            SET file_extension = SUBSTRING_INDEX(file_name, '.', -1)
                            WHERE task_id = %s
                        """
                        cursor.execute(update_file_ext_query, (task_id,))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with file extension.")
                    except Exception as e:
                        logging_module.log_error(f"Error updating file extension for task_id {task_id}: {e}")

                else:
                    logging_module.log_error(f"Failed to download {file_name}: HTTP {response.status_code}")

            except requests.exceptions.RequestException as e:
                logging_module.log_error(f"Error downloading {file_name}: {e}")

except Error as e:
    logging_module.log_error(f"Error while connecting to MySQL: {e}")

finally:
    try:
        if connection.is_connected():
            cursor.close()
            connection.close()
            logging_module.log_success("MySQL connection is closed.")
    except Exception as e:
        logging_module.log_error(f"Error closing MySQL connection: {e}")
