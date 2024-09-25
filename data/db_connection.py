# This Python script establishes a connection to an AWS RDS MySQL database using environment variables for 
# credentials and connection details. It securely loads these variables using the `dotenv` package and 
# defines a function `get_db_connection()` to create and return a connection object, facilitating database 
# interactions within the application.

import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

# Getting in Environmental variables
aws_rds_host=os.getenv('AWS_RDS_HOST')
aws_rds_user=os.getenv('AWS_RDS_USERNAME')
aws_rds_password=os.getenv('AWS_RDS_PASSWORD')
aws_rds_port =os.getenv('AWS_RDS_DB_PORT')
aws_rds_database = os.getenv('AWS_RDS_DATABASE')

def get_db_connection() -> mysql.connector.connection_cext.CMySQLConnection:
    """
    Establishes and returns a connection to the AWS RDS MySQL database using the provided credentials.

    Returns:
        mysql.connector.connection_cext.CMySQLConnection: A MySQL database connection object.
    """
    return mysql.connector.connect(
        host= aws_rds_host,
        user=aws_rds_user,
        password=aws_rds_password,
        port =aws_rds_port,
        database=aws_rds_database
    )