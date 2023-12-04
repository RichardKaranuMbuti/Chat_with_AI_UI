import pandas as pd
from sqlalchemy import create_engine

# Replace the following with your MySQL server details
username = 'your_username'
password = 'your_password'
host = 'localhost'  # or your server IP
database_name = 'metakocka_db'

# Creating the database connection
engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}/')

# Create a new database (if it doesn't exist)
with engine.connect() as conn:
    conn.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
    conn.execute(f"USE {database_name}")

# Read data from Excel file
df = pd.read_excel('Metakocka.xlsx', engine='openpyxl')

# Data cleaning or manipulation here if needed

# Creating the table and inserting data
# The table name is 'FinancialBookTransactions'
df.to_sql('FinancialBookTransactions', con=engine, if_exists='replace', index=False)

print("Data imported successfully.")
