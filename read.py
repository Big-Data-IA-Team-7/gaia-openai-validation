import mysql.connector
import pandas as pd

def fetch_data_from_db():
    try:
        # Connect to MySQL database
        mydb = mysql.connector.connect(
            host='bdia-team7-database.cf0yua88qmrg.us-east-1.rds.amazonaws.com',
            port='3306',
            user='bdia_team_7',
            password='Bigdatateam7',
            database='bdia_team7_db'
        )
        
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

