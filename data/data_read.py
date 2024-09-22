import mysql.connector
import pandas as pd
from data.db_connection import get_db_connection
from datetime import datetime
from mysql.connector import Error

def fetch_data_from_db():
    try:
        # Connect to MySQL database
        mydb = get_db_connection()
        
        if mydb.is_connected():
            print("Connected to the database")

            # Create a cursor object
            mydata = mydb.cursor()

            # Execute the query
            mydata.execute("SELECT * FROM gaia_metadata_tbl")
            
            # Fetch all the data
            myresult = mydata.fetchall()

            # Get column names
            columns = [col[0] for col in mydata.description]

            # Store the fetched data into a pandas DataFrame
            df = pd.DataFrame(myresult, columns=columns)

            return df

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

    finally:
        if mydb.is_connected():
            mydata.close()
            mydb.close()
            print("MySQL connection closed")

#Fetching the data for the dasboards
def fetch_data_from_db_dashboards():
    try:
        # Connect to MySQL database
       # Connect to MySQL database
        mydb = get_db_connection()
        
        if mydb.is_connected():
            print("Connected to the database")

            # Create a cursor object for dashboards
            mydata_dashboard = mydb.cursor()

            # Execute the query values for dashboards
            mydata_dashboard.execute("SELECT * FROM model_response")

            # Fetch all the data for dashboards
            myresult = mydata_dashboard.fetchall()

            # Get column names
            columns = [col[0] for col in mydata_dashboard.description]

            # Store the fetched data into a pandas DataFrame
            df_dashboards = pd.DataFrame(myresult, columns=columns)

            return df_dashboards

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

    finally:
        if mydb.is_connected():
            mydata_dashboard.close()
            mydb.close()
            print("MySQL connection closed")

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