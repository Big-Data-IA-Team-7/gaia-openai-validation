import boto3
import pandas as pd
from urllib.parse import urlparse
from read import fetch_data_from_db
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader  # For PDF handling
import io

# Load .env file
load_dotenv()

# AWS credentials
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)

def parse_s3_url(url):
    """Parse the S3 URL to extract bucket name and object key."""
    parsed_url = urlparse(url)
    bucket_name = parsed_url.netloc.split('.')[0]  # Extract bucket name
    object_key = parsed_url.path.lstrip('/')       # Extract object key
    return bucket_name, object_key

def generate_presigned_url(s3_url, expiration=3600):
    """Generate a pre-signed URL for an S3 object."""
    bucket_name, object_key = parse_s3_url(s3_url)
    
    try:
        # Generate pre-signed URL that expires in the given time (default: 1 hour)
        presigned_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': object_key},
                                                  ExpiresIn=expiration)
        return presigned_url
    except Exception as e:
        print(f"Error generating pre-signed URL: {e}")
        return None
# Fetch data from the database
df = fetch_data_from_db()

def process_data_and_generate_url(Question):
    """Fetch data from DB, extract S3 URL, and generate a pre-signed URL if available."""
    
    if df is not None:
        if 's3_url' in df.columns:
            # Extract the S3 URL for the specified Question
            matching_rows = df[df['Question'] == Question]
            if not matching_rows.empty:
                s3_url_variable = matching_rows['s3_url'].values[0]

                # Check if s3_url_variable is null
                if s3_url_variable!='':
                    # Generate a pre-signed URL for the S3 file
                    presigned_url = generate_presigned_url(s3_url_variable, expiration=3600)  # URL valid for 1 hour
                    return presigned_url
                else:
                    print("No File is associated with this Question")
                    return 1
            else:
                print("No matching Question found")
                return 1
        else:
            print("'s3_url' column not found in DataFrame")
            return 1
    else:
        print("Failed to fetch data from the database")
    
    
