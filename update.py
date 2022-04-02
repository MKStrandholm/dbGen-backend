import flask
from flask import Blueprint, make_response, jsonify
import psycopg2
from connection import connect_to_db
from collections import ChainMap

update_endpoint = Blueprint('update_endpoint', __name__)
@update_endpoint.route('/update/<table_name>', methods=['POST'])

def update(table_name):
    '''
    This function is the default method of the update endpoint. It takes in a parameter of table name which tells the endpoint which table to
    refer to for the update process
    
     Keyword Arguments:
        table_name       --      The name of the table passed into the URL by the front-end, this is used
        to establish the route
        
    return   --   returns a JSON formatted object that includes the information about the record that was updated and whether or not
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
    oldData = []
    newData = []
    
    # Save request body into a variable
    record = flask.request.json
    # Split the request body into its corresponding pieces
    oldRecord = record['old']
    newRecord = record['new']
    
     # Make sure we don't try to update a record if the request is invalid (either one of the old/new objects or the wrapper object as a whole)
    if (
        (record != {} and record != "undefined" and record is not None) and
        (oldRecord != {} and oldRecord != "undefined" and oldRecord is not None) and
        (newRecord != {} and newRecord != "undefined" and newRecord is not None)):
        
        # If objects are mismatched in props length, inform the user
        if (len(oldRecord) == len(newRecord)):
        
            # Save new data values
            for i in newRecord:
                newData.append(newRecord.get(i))
            
            # Iterate through the old record and grab the amount of fields, the fields themselves and the values so we can pinpoint the exact record
            for i in oldRecord:
                value_count += '%s, '
                fields.append(i)
                oldData.append(oldRecord.get(i))
            
            # Start the query by using the update <table> syntax
            query = f"UPDATE {table_name} SET "
            
            # Iterate through each field of the new data and append its field name & value to the query (setting new values)
            for i in range(0, len(fields)):
                query += fields[i] + '=' + "'" + newData[i] + "'" + ", "
            
            # Trim the space and comma
            query = query[:-2]
            query += " WHERE "

            # Iterate through each field of the old data and append its field name & value to the query (where condition)
            for i in range(0, len(fields)):
                query += fields[i] + '=' + "'" + oldData[i] + "'" + " AND "
            
            # Trim the last ' and ' since it's unneeded
            query = query[:-5]
            
            print(query)
                
            try:
                cur.execute(query)
                conn.commit()
                
                # Create an empty list of objects that will contain the field:value dictionaries, so we can chainmap them into 1
                fieldObjects = []  
                
                # Iterate through the field list and create a new object, mapping the field name to the data value
                for i in range(0, len(fields)):
                    fieldObject = {
                        fields[i]:newData[i]
                    }
                    # Append this object to the list above
                    fieldObjects.append(fieldObject)
                
                # Create an object by merging the field objects into a single dictionary
                responseObject = dict(ChainMap(*fieldObjects))
                
                # Update the res object with the proper success value, message and data object that we merged above
                res = {
                    "success": True,
                    "message": f"Successfully updated record in {table_name} table.",
                    "data": responseObject
                }
                
                # Output a message to the terminal with the response object created
                print(f"UPDATE SUCCESSFUL:\n", responseObject)
                
                # Return the res object
                return jsonify(res)

            # If an exception occurred, return the error and 400 code
            except (Exception, psycopg2.DatabaseError) as error:
                    print(f"UPDATE FAILED:\n", error.pgerror)
                    res = {
                    "success": False,
                    "message": f"Failed to update record in {table_name} table: " + str(error.pgerror)
                    }
                    return make_response(jsonify(res), 400) 
            finally:
                # If there is a current connection object, close both the cursor and the connection as they're unneeded now
                if conn:
                    cur.close()
                    conn.close()
        # Old and new record objects field count mismatched, bad request    
        else:
            print(f"UPDATE FAILED:\n", "New and old record objects are mismatched in length. You may have forgotten a property in either object.")
            res = {
                "success": False,
                "message": f"Failed to update record in {table_name} table: new and old record objects are mismatched in length"
            }
            return make_response(jsonify(res), 400)
    # Empty or invalid request body
    else:
        print(f"UPDATE FAILED:\n", "Request body or its children objects empty or invalid")
        res = {
            "success": False,
            "message": f"Failed to update record in {table_name} table: request body or its children objects empty or invalid"
        }
        return make_response(jsonify(res), 400)