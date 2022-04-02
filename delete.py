import flask
from flask import Blueprint, make_response, jsonify
import psycopg2
from connection import connect_to_db
from collections import ChainMap

delete_endpoint = Blueprint('delete_endpoint', __name__)

@delete_endpoint.route('/delete/<table_name>', methods=['POST'])

def delete(table_name):
    '''
    This function is the default method of the delete endpoint. It takes in a parameter of table name which tells the endpoint which table to
    delete from
    
     Keyword Arguments:
        table_name       --      The name of the table passed into the URL by the front-end, this is used
        to establish the route
        
    return   --   returns a JSON formatted object that includes the information about the record that was deleted and whether or not
                    the operation was a success
    '''
    # Establish connection to database
    conn = connect_to_db()
    cur = conn.cursor()
    # Create a placeholder response object for now that will be updated when this process completes
    res = {}
    
     # Create placeholder variables for the record fields/data/values (SQL placeholder strings [%s] - this is to keep track of how many values must be provided)
    value_count = ""
    fields = []
    data = []
    
    # Save the request body for easy accessing
    record = flask.request.json
    
    # Make sure we don't try to delete a record if the request is invalid
    if record != {} and record != "undefined" and record is not None:
        
        # Iterate through the record and grab the amount of fields, the fields themselves and the values so we can pinpoint the exact record
        for i in record:
            value_count += '%s, '
            fields.append(i)
            data.append(record.get(i))
        
        # Start the query by using the update <table> syntax
        query = f"DELETE FROM {table_name}"
        
        # Append the 'where' keyword
        query += " WHERE "

        # Iterate through each field of the old data and append its field name & value to the query (where condition)
        for i in range(0, len(fields)):    
            query += fields[i] + '=' + "'" + data[i] + "'" + " AND "
        
        # Trim the last ' and ' since it's unneeded
        query = query[:-5]
            
        try:
            cur.execute(query)
            conn.commit()
            
            # Create an empty list of objects that will contain the field:value dictionaries, so we can chainmap them into 1
            fieldObjects = []  
            
            # Iterate through the field list and create a new object, mapping the field name to the data value
            for i in range(0, len(fields)):
                fieldObject = {
                    fields[i]:data[i]
                }
                # Append this object to the list above
                fieldObjects.append(fieldObject)
            
            # Create an object by merging the field objects into a single dictionary
            responseObject = dict(ChainMap(*fieldObjects))
            
            # Update the res object with the proper success value, message and data object that we merged above
            res = {
                "success": True,
                "message": f"Successfully deleted record in {table_name} table.",
                "data": responseObject
            }
            
            # Output a message to the terminal with the response object created
            print(f"DELETE SUCCESSFUL:\n", responseObject)
            
            # Return the res object
            return jsonify(res)

       # If an exception occurred, return the error and 400 code
        except (Exception, psycopg2.DatabaseError) as error:
                print(f"DELETE FAILED:\n", error.pgerror)
                res = {
                "success": False,
                "message": f"Failed to delete record from {table_name} table: " + str(error.pgerror)
                }
                return make_response(jsonify(res), 400) 
        finally:
            # If there is a current connection object, close both the cursor and the connection as they're unneeded now
            if conn:
                cur.close()
                conn.close()
    # Request was empty or invalid
    else:
        print(f"DELETE FAILED:\n", "Request body empty or invalid")
        res = {
            "success": False,
            "message": f"Failed to delete record in {table_name} table: request body was empty or invalid"
        }
        return make_response(jsonify(res), 400)