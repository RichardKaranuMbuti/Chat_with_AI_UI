import pandas as pd
from sqlalchemy import create_engine
import os 
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv() 

# Replace the following with your MySQL server details
username = os.getenv("db_user")
password = os.getenv("password")
host = os.getenv("db_host")
database_name = 'metakocka_db'

# Creating the database connection
engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/{database_name}')

# Create a new database (if it doesn't exist)
with engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
    conn.execute(text(f"USE {database_name}"))
# Read data from Excel file
df = pd.read_excel('Metakocka.xlsx', engine='openpyxl')

# Data cleaning or manipulation here if needed

# Creating the table and inserting data
# The table name is 'FinancialBookTransactions'
df.to_sql('FinancialBookTransactions', con=engine, if_exists='replace', index=False)

print("Data imported successfully.")

