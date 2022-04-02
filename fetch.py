import json
import flask
from flask import Blueprint, make_response, jsonify
import psycopg2
from psycopg2 import sql
from connection import connect_to_db

fetch_endpoint = Blueprint('fetch_endpoint', __name__)
# Create an endpoint for fetching all tables in the database
@fetch_endpoint.route('/<schema>/tables', methods=['GET'])
    
def home(schema):  
    '''
    This function is the default method of the /tables endpoint. It grabs all of the table names in the database
    and then subsequently grabs every record from each table. It then structures the data in the decided JSON format which will be then accessed
    by the front-end

    return   --   returns a JSON formatted list of table objects, their names, prefixes and fields
    '''  
        ### SETUP ###
    
    # Empty list that will hold the table objects as they get created
    tableObjects = []
    # Setup connection and DB cursor
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        # First grab all of the table information (names)
        cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema=%(schema)s ORDER BY table_name;""", {"schema": schema})
        tableData = cur.fetchall()
        
        # This query finds all foreign key constraints with information about the tables and fields that make up this constraint
        query = sql.SQL("SELECT tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name WHERE constraint_type = 'FOREIGN KEY'")
        cur.execute(query)
        # Save the constraints into a list for later
        foreignConstraints = cur.fetchall()
               
        ### DATA EXTRACTION ###     
        
        # Empty table and field lists that will be appended to as this method runs    
        tables = []
        fields = []
        # Browse through each table name, ensuring we skip over prefixes (which is a helper table)
        for tableName in tableData:
            tableName = tableName[0]
            if (tableName != 'prefixes'):
                # For tables that are NOT the prefix table, grab information about the table itself, the columns within, and their respective datatypes/any user imposed lengths
                query = sql.SQL("SELECT table_name, column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_schema = 'public' AND table_name != 'prefixes' ORDER BY ordinal_position")
                cur.execute(query)
                # Save this data so we can scrub through it
                fieldData = cur.fetchall()
                
                # Avoid duplicate fields, this ensures we always have the correct amount of fields per table
                for field in fieldData:
                    if (field not in fields):
                       fields.append(field)
              
        # Iterate through each field and append the table names to the tables list (this prevents duplicates as well)      
        for field in fields: 
            if (field[0] not in tables):
                tables.append(field[0])
     
        # Iterate through all of the tables and create objects with their appropriate values
        for table in tables:
            # Grab table prefix first and foremost
            cur.execute("""SELECT relationship_prefix FROM prefixes WHERE table_name = %(table)s;""", {'table': table})
            table_prefix = cur.fetchone()
            tableFields = []
            for field in fields:
                # If the current field belongs to the table in question, grab the table_field prefix (usually 'employee_', throwing away the underscore) and link the field prefix to the table prefix using the prefixes table. Now, each field (and table) has its prefix identified correctly
                if (field[0] == table):               
                    cur.execute("""SELECT relationship_prefix FROM prefixes WHERE table_field_prefix = %(prefix)s;""", {'prefix': field[1].split('_')[0]})
                    prefix = cur.fetchone()
                    if table_prefix == "":
                        table_prefix = prefix
                    
                    # If there are foreign constraints that were identified earlier, look through their information to identify which tables/field they belong to
                    if (len(foreignConstraints) > 0):
                        # Iterate through each foreign constraint and check its table name against our current table, and its field name against our current field. We currently don't need to understand the referenced table, so just the table the constraint is on will suffice
                        for i in range(0, len(foreignConstraints)):
                            # If both the table and field match our current table/field, we've identified which field is a foreign key and can toggle the flag
                            if (foreignConstraints[i][1] == table and foreignConstraints[i][2] == field[1]):
                                isFK = True
                                break
                            else:
                                isFK = False
                    # Create the field object with the above properties
                    fieldObject = {
                        "field_name": field[1],
                        "field_prefix": prefix[0],
                        "field_type": {
                          "type": field[2],
                          "length":field[3]
                        },
                      "isForeign": isFK,
                      "isPrimary": False 
                    }
                    # Append this field object to the table fields list
                    tableFields.append(fieldObject)

            # Now, grab the records from each table so we can append them to the table object to display on the front-end
            cur.execute(f"SELECT * FROM {table};")
            tableRecordsRaw = cur.fetchall()
            
            # Create empty lists to hold the field names and the tuples created with them
            field_names = []
            field_name_tuple_list = []
            
            # Iterate through the length of table fields and append their actual name to the field_names list
            for i in range(0, len(tableFields)):
                field_names.append(tableFields[i]['field_name'])
                
            # Iterate through the length of table records and append a tuple with this table's field names to match the # of records
            for i in range(0, len(tableRecordsRaw)):
                field_name_tuple_list.append(tuple(field_names))
             
            # Create an empty list to hold the zipped dictionary   
            zipped = []
            
            # Iterate through the length of the tuple list and zip together (1:1) the field names with the record tuples
            # (ex. Let's say we have 3 records in a table which are stored in an array as tuples:
            #       [
            #           (1, "Bob", 1)
            #           (2, "Frank", 2)
            #           (3, "Sarah", 3)
            #       ]
            #
            # These are the tuples obtained from the database, and we need to combine them with the field names so we create
            # a similarly structured tuple of field names:
            #       [
            #           ('id', 'name', 'job_id')
            #           ('id', 'name', 'job_id')
            #           ('id', 'name', 'job_id')
            #       ]
            #
            # It's a tacky solution at best, but by zipping these tuples we obtain something structured like a real JSON record (dict):
            #
            #       [
            #           {
            #               "id": 1,
            #               "name": "Bob",
            #               "job_id": 1
            #           },
            #           {   
            #               "id": 2,
            #               "name": "Frank",
            #               "job_id": 2
            #           },
            #           {
            #               "id": 3,
            #               "name": "Sarah",
            #               "job_id": 3
            #           },
            #       ]   
            for i in range(0, len(field_name_tuple_list)):
                zipped.append(dict(zip(field_name_tuple_list[i], tableRecordsRaw[i])))
                
            # Create the table object with the above properties
            tableObject = {
                "table_name":table,
                "table_prefix": table_prefix[0],
                "table_fields": tableFields,
                "table_records": zipped
            }
            
            # Append the table object to the table list
            tableObjects.append(tableObject)

        res = {
            "success": True,
            "data": tableObjects
        }
        
        print("FETCH SUCCESSFUL:\n", tableObjects)
        return jsonify(res)
    # If an exception occurred, return the error and 400 code
    except (Exception, psycopg2.DatabaseError) as error:
        print("FETCH FAILED:\n", error.pgerror)
        res = {
            "success": False,
            "message": f"Failed to grab records from database" + str(error.pgerror)
        }
        return make_response(jsonify(res), 400) 
    finally:
        if conn:
            cur.close()
            conn.close()