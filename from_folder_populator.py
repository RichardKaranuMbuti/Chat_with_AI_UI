import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

# Replace the following with your MySQL server details
username = os.getenv("db_user")
password = os.getenv("db_password")
host = os.getenv("db_host")
database_name = os.getenv("db_name2")

# Creating the database connection string
connection_string = f'mysql+mysqlconnector://{username}:{password}@{host}/'

# Create engine outside of the database scope
engine = create_engine(f"{connection_string}")

# Function to sanitize column names for MySQL
def sanitize_column_names(df):
    df.columns = df.columns.str.strip().str.replace(' ', '_', regex=True).str.replace(r'\W', '', regex=True)
    return df

# Function to create database if it does not exist
def create_database(engine, database_name):
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
        print(f"Database '{database_name}' is ready.")
    except SQLAlchemyError as e:
        print(f"Error creating database: {e}")

# Function to process CSV files in a folder
def process_csv_files(folder_path, engine, database_name):
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            file_path = os.path.join(folder_path, file)
            table_name = os.path.splitext(file)[0].replace(' ', '_')  # Sanitize table name
            try:
                df = pd.read_csv(file_path, low_memory=False)
                df = sanitize_column_names(df)  # Sanitize column names

                # Write the DataFrame to the SQL database without date parsing
                df.to_sql(name=table_name, con=engine, if_exists='replace', index=False, chunksize=1000)
                print(f"Data from {file} has been imported into {table_name}.")
            except Exception as e:
                print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    # Path to the folder containing your CSV files
    folder_path = 'data'  # Replace with the path to your folder

    # Create the database (if it doesn't exist)
    create_database(engine, database_name)

    # Adjust engine for the specific database
    engine = create_engine(f"{connection_string}{database_name}")

    # Process CSV files
    process_csv_files(folder_path, engine, database_name)
