# This Python script provides utility functions for interacting with AWS S3 services using the Boto3 library.
# It includes functionality for parsing S3 URLs, handling different file extensions, and generating presigned URLs 
# for accessing S3 objects. The script initializes the S3 client using AWS credentials from environment variables 
# and facilitates the seamless integration of S3 data within the application, with logging incorporated for monitoring purposes.

import boto3
from urllib.parse import urlparse, unquote
import os
import requests
import tempfile
from project_logging import logging_module

# File Extensions
RETRIEVAL_EXT = ['.docx', '.txt', '.pdf', '.pptx']
CI_EXT = ['.csv', '.xlsx', '.py', '.zip']
IMG_EXT = ['.jpg', '.png']
ERR_EXT = ['.pdb', '.jsonld']
MP3_EXT = ['.mp3']

# AWS credentials
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)

def parse_s3_url(url: str) -> tuple:
    """
    Parses an S3 URL to extract the bucket name and object key.

    Args:
        url (str): The S3 URL to be parsed.

    Returns:
        tuple: A tuple containing the bucket name (str) and the object key (str).
    """
    parsed_url = urlparse(url)
    bucket_name = parsed_url.netloc.split('.')[0]  # Extract bucket name
    object_key = parsed_url.path.lstrip('/')       # Extract object key
    return bucket_name, object_key

def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Generates a pre-signed URL for an S3 object that allows temporary access.

    Args:
        s3_url (str): The S3 URL of the object (e.g., 'https://bucket-name.s3.amazonaws.com/object-key').
        expiration (int, optional): The time in seconds until the pre-signed URL expires. Defaults to 3600 seconds (1 hour).

    Returns:
        str: The pre-signed URL allowing temporary access to the S3 object, or None if an error occurs.
    """
    bucket_name, object_key = parse_s3_url(s3_url)
    
    try:
        # Generate pre-signed URL that expires in the given time (default: 1 hour)
        presigned_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': object_key},
                                                  ExpiresIn=expiration)
        return presigned_url
    except Exception as e:
        logging_module.log_error(f"Error generating pre-signed URL: {e}")
        return None

def process_data_and_generate_url(question: str, df) -> str:
    """
    Fetches data from the database, extracts the S3 URL for the specified question, and generates a pre-signed URL if available.

    Args:
        question (str): The question for which the associated S3 URL needs to be retrieved.

    Returns:
        str: A pre-signed URL for the S3 file if available.
    """
    if df is not None:
        if 's3_url' in df.columns:
            # Extract the S3 URL for the specified Question
            matching_rows = df[df['Question'] == question]
            if not matching_rows.empty:
                s3_url_variable = matching_rows['s3_url'].values[0]
                logging_module.log_success(f"S3 URL: {s3_url_variable}")

                # Check if s3_url_variable is null
                if s3_url_variable is not None:
                    # Generate a pre-signed URL for the S3 file
                    presigned_url = generate_presigned_url(s3_url_variable, expiration=3600)  # URL valid for 1 hour
                    return presigned_url
                else:
                    logging_module.log_success("No File is associated with this Question")
                    return "1"
            else:
                logging_module.log_error("No matching Question found")
                return "1"
        else:
            logging_module.log_error("'s3_url' column not found in DataFrame")
            return "1"
    else:
        logging_module.log_error("Failed to fetch data from the database")
 
def download_file(url: str) -> dict:
    """
    Downloads a file from the given URL and saves it as a temporary file with the appropriate extension.

    Args:
        url (str): The URL of the file to be downloaded.

    Returns:
        dict: A dictionary containing the following keys:
            - "url" (str): The original URL of the file.
            - "path" (str): The path to the downloaded temporary file.
            - "extension" (str): The file extension of the downloaded file.
    """
    # Parse the URL to extract the file name
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    filename = os.path.basename(path)
    extension = os.path.splitext(filename)[1]
    
    # Create a temporary file with the correct extension
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    
    # Get the file from the URL
    response = requests.get(url)
    response.raise_for_status()  # Check if the download was successful
    
    # Write the content to the temporary file
    temp.write(response.content)
    temp.close()  # Close the file to finalize writing
    
    return {"url": url, "path": temp.name, "extension": extension}