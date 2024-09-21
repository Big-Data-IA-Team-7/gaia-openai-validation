import os
import mysql.connector



# Getting in Environmental variables
aws_rds_host=os.getenv('AWS_RDS_HOST')
aws_rds_user=os.getenv('AWS_RDS_USERNAME')
aws_rds_password=os.getenv('AWS_RDS_PASSWORD')
aws_rds_port =os.getenv('AWS_RDS_DB_PORT')
aws_rds_database = os.getenv('AWS_RDS_DATABASE')



def get_db_connection():
    return mysql.connector.connect(
        host= aws_rds_host,
        user=aws_rds_user,
        password=aws_rds_password,
        port =aws_rds_port,
        database=aws_rds_database
    )