import flask
from flask import Blueprint, jsonify, make_response
import psycopg2
from connection import connect_to_db
from collections import ChainMap

create_endpoint = Blueprint('create_endpoint', __name__)
@create_endpoint.route('/create/<table_name>', methods=['POST'])

def create(table_name):
    '''
    This function is the default method of the create endpoint. It takes in a parameter of table name which tells the endpoint which table to
    insert into
    
     Keyword Arguments:
        table_name       --      The name of the table passed into the URL by the front-end, this is used
        to establish the route
        
    return   --   returns a JSON formatted object that includes the information about the record that was created and whether or not
                    the operation was a success
    '''
    # Establish connection to database
    conn = connect_to_db()
    cur = conn.cursor()
    # Create a placeholder response object for now that will be updated when this process completes
    res = {}
    
    # Create placeholder variables for the record fields/data/values (SQL placeholder strings [%s] - this is to keep track of how many values must be provided)
    fields = ""
    value_count = ""
    data = []
    
    # Save record as variable
    record = flask.request.json
    
    # Inform user that request is bad if it is
    if (record != {} and record != "undefined" and record is not None):
        # Iterate through the request body and append the field name followed by a comma and space (to adhere to PostgreSQL convention), as well 
        # as the value count (using %s placeholders) and data values
        for i in flask.request.json:
            fields += i + ', '
            value_count += '%s, '
            data.append(flask.request.json[i])
        # Remove the last 2 characters from the fields and value count strings (these are just a space and a comma that are unneeded)
        fields = fields[:-2]
        value_count = value_count[:-2]
    
        # Attempt to grab the prefix that aligns with this table, so we can check for a singular PK ID (self-referencing ID)
        try: 
            cur.execute("""SELECT table_field_prefix FROM prefixes WHERE table_name = %(table)s;""", {'table': table_name})
            prefix = cur.fetchone()
            prefix = prefix[0]

        except(Exception, psycopg2.DatabaseError) as error:
             print("CREATE FAILED:\n", error.pgerror)
            
        # Attempt the insert the record into the database using the above information
        try:
            # Establish a new record ID variable that may be updated if this table has a self-referencing PK ID
            new_record_id = ""
            # Attempt to insert and return a self-referencing PK IDs (ex. emp_id in an employees table)
            try:
                # If a PK ID was found, return it with the response for the front-end
                query = f"INSERT into {table_name}({fields}) VALUES ({value_count}) RETURNING {prefix}_id"
                cur.execute(query, data)
                # Grab the records ID that was generated
                new_record_id = cur.fetchone()[0]
            # No PK ID found, it's a compound table so just rollback the previous (failed) transaction and insert normally
            except(Exception, psycopg2.DatabaseError) as error:
                print("Failed to return self-referencing PK ID, compound table detected: inserting record as normal with no return value")
                cur.execute("ROLLBACK")
                conn.commit()
                query = f"INSERT into {table_name}({fields}) VALUES ({value_count})"
                cur.execute(query, data)
          
            conn.commit()
            
            # Create an empty list of objects that will contain the field:value dictionaries, so we can chainmap them into 1
            fieldObjects = []  
            # Split the field list string so we have a list of fields to match a list of values (data)
            fieldList = fields.split(', ')
            
            # Iterate through the field list and create a new object, mapping the field name to the data value
            for i in range(0, len(fieldList)):
                # If a new record ID was determined (this is a table with a singular PK ID), append it to the object for the front-end
                if new_record_id != "":
                    fieldObject = {
                        prefix + "_id": new_record_id,
                        fieldList[i]:data[i]
                    }
                # Compound key table, no ID can be passed
                else: 
                    fieldObject = {
                        fieldList[i]:data[i]
                    }
                # Append this object to the list above
                fieldObjects.append(fieldObject)
            
            # Create an object by merging the field objects into a single dictionary
            responseObject = dict(ChainMap(*fieldObjects))
            
            # Update the res object with the proper success value, message and data object that we merged above
            res = {
                "success": True,
                "message": f"Successfully inserted record into {table_name} table.",
                "data": responseObject
            }
            
            # Output a message to the terminal with the response object created
            print(f"CREATE SUCCESSFUL:\n", responseObject)
            
            # Return the res object
            return jsonify(res)

        # If an exception occurred, return the error and 400 code
        except (Exception, psycopg2.DatabaseError) as error:
                print("CREATE FAILED:\n", error.pgerror)
                res = {
                "success": False,
                "message": f"Failed to insert record into {table_name} table: " + str(error.pgerror)
                }
                return make_response(jsonify(res), 400) 
        finally:
            # If there is a current connection object, close both the cursor and the connection as they're unneeded now
            if conn:
                cur.close()
                conn.close()
    # Request body is empty or invalid
    else:
        print(f"CREATE FAILED:\n", "Request body empty or invalid")
        res = {
            "success": False,
            "message": f"Failed to create record in {table_name} table: request body empty or invalid"
        }
        return make_response(jsonify(res), 400)