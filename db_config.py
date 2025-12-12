import os
from dotenv import load_dotenv
import mysql.connector

# Load variables from .env file
load_dotenv() 

def get_connection():
    """Establishes and returns a MySQL database connection."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except mysql.connector.Error as err:
        # Handle connection errors gracefully
        print(f"Error connecting to MySQL: {err}")
        return None