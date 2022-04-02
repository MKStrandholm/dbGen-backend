from dotenv import load_dotenv, find_dotenv
import psycopg2
import os

def connect_to_db():
    '''
    This function establishes a connection to the postgres database

    return   --   returns a connection object that is used to perform SQL queries
    '''
    
    load_dotenv(find_dotenv())
    
    conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'))
    
    return conn