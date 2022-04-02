import json

from objects.Table import Table
from objects.Field import Field

def read_script(filename):
    '''
    The function takes in a SQL script file and reads the blocks which will be used in the processing method. A block ends with ');'
    Keyword arguments:
    filename    --  The SQL script file that will be parsed

    return      --   returns a 2D list (SQL blocks)
    '''
    sql_blocks = []
    current_block = []
    
    # Read the file
    with open(filename, 'r') as file:
        # Iterate through each line and strip away newlines
        keyword_list = ["PRIMARY","CONSTRAINT","FOREIGN", "REFERENCES"]
        for line in file:
            stripped_line = str.rstrip(line)
            omit_line = False
            #This list contains the key words of lines that will be omitted for this script.
            #This flag will omit a line that contains relationships that will not be used for the script.
            input_words = line.split()
            for word in input_words:
                if word in keyword_list:
                    omit_line = True
                    break
    
            # If the current line is the closing brace, the block is complete so we should append the current_block list (the sql block)
            # to the sql_blocks list and reset it
            if stripped_line == ');':
                sql_blocks.append(current_block)
                current_block = []
            #When a line that contains infromation not required by the script is found, omit it.
            elif omit_line:
                continue
            # Not a closing brace, this is part of a sql block so we'll add it to the current_block list
            else:
                current_block.append(stripped_line)
    file.close()
    return sql_blocks

def process_sql_blocks(sql_blocks, table_list):
    '''
    The function takes list of sql blocks from the read method and processes their information into Table objects
    Keyword arguments:
    sql_blocks    --   The 2D list of sql blocks read from the previous method
    table_list    --   The final list of tables that will be appended to

    return      --   Nothing
    '''
    
    # Iterate through each sql block
    for i in range(len(sql_blocks)):
     
        # These lists will store the cleaned lines/blocks after cleaning passes
        cleaned_lines = []
        cleaned_blocks = []
        
        # This list will store the header information
        table_commands_and_name = []
        # This list will store the information about each field
        fields_data = []

        # Cleanup empty indices
        if (sql_blocks[i][0] == ''):
            sql_blocks[i].pop(0)
        
        # Iterate through each item in the first line and purge all double quotes that were carried over from read (as well as stray commas, etc.)
        for item in sql_blocks[i][0]:
            # Get rid of double quotes in header
            header_clean_pass_one = item.replace('"', '')
            table_commands_and_name.append(header_clean_pass_one)
        # Get rid of double quotes and commas in fields
        for item in sql_blocks[i]:
            clean_pass_one = item.replace('"', '')
            clean_pass_two = ""
            comma_found = False
            #remove last comma only if the string contains it.
            l=len(clean_pass_one)
            if clean_pass_one[l-1] == ",":
                comma_found = True
                clean_pass_two = clean_pass_one[:l-1] #this variable must be stored or it won't save the shortening of the string.
            '''
            Below, we have 2 flags, one for a string that did not contain a comma at the end
            but still needs to be added to the list. Another, that had a comma at the end and
            was filtered our of the string.

            This process must be used because, if we were to use the replace() method,
            it would eliminate the comma that defines a float value as well, giving us 
            an undesired output.
            '''
            # In case of any indices with a value of '', we want to skip it
            if (clean_pass_one != "" and not comma_found):
                # Not an empty string, so append this cleaned line
                cleaned_lines.append(clean_pass_one)
            if (clean_pass_one != "" and comma_found):
                cleaned_lines.append(clean_pass_two)
        # Now that all lines have been cleaned, add them to the cleaned blocks list and reset it for the next table
        cleaned_blocks.append(cleaned_lines)
        cleaned_lines = []
        
        # Final clean-up of header (joining single chars into 1 string, removing stray parentheses)
        cleaned_header = ''.join(table_commands_and_name)
        cleaned_header = cleaned_header.replace(' (', '')
        
        # Loop and get the table fields
        for line in cleaned_blocks:
            # Remove the first item as its the header information, this leaves us with an array of fields
            line.pop(0)
            fields_data.append(line)

        # Split the cleaned header into a list of items (query, entity, prefix.name)
        segmented_header = cleaned_header.split(' ')
        # Create a list to store the segmented fields in
        segmented_fields = []
        # Iterate through all of the field data and segment it in a similar approach to the header (prefix, name, datatype)
        for field in fields_data[0]:
            field = field.split(' ')
            # Append each split field item into the segmented fields list so we can pass it into the Table constructor in a 
            # format it's expecting
            segmented_fields.append(field)
        
        # Create the Table object with the parsed information and append it to the master table list
        table_object = create_table(segmented_header, segmented_fields)
        table_list.append(table_object)
    

def create_table(table_information, fields_information):
    '''
    The function takes the contents of the table and its fields to generate the respective objects
    Keyword arguments:
    table_information    --   The name and prefix of the table
    fields_information   --   The list of table fields and their prefix/name/type/PK flag/FK flag

    return      --   returns a Table object
    '''
    
    # Extract prefix, name from table info
    table_prefix, table_name = table_information[2].split('.')
    field_list = []


    for table_field in fields_information:
        #delete the 2 whitespace that have been added to the list because of indentation
        while table_field[0] == "":
            del table_field[0]
        # Initial states of bool flags which will be given to the Field object constructor
        primary = False
        foreign = False
        # You can expect this array to look something like: 
        # [0] - prefix
        # [1] - field name
        prefix, name = table_field[0].split('.')
        type = table_field[1]

        # Different prefix found, this is a FK
        if prefix != table_prefix:
            foreign = True
        
        # If its the first field, assume its a PK
        if table_field == fields_information[0]:
            primary = True
            
        # Create a Field object with this data and append it to the field list of the table
        field_list.append(Field(prefix, name, type, foreign, primary).__dict__)
    # Build the Table object with the information gathered
    table = Table(
        table_prefix,
        table_name,
        field_list
    ).__dict__
    
    return table


def assign_compound_keys(table_list):
    '''
    Based on requirements by the client, the compound keys will be identified based on
    the location of the fields that have a prefix of the table. Any key that is located 
    before a field with this prefix can be considered as part of a compound key.

    Once the location is found, we assignt the attribute isPrimary to be True 
    to the preceding Field objects.
    '''
    for table in table_list:
        position_index = 0
        compound_end_point = 0
        #get the dictionary of Field objects from the table
        fields_list = table['table_fields']
        #loop through and compare prefixes to find compound keys and save their position
        for field in fields_list:
            if field['field_prefix'] == table['table_prefix']:
                compound_end_point = position_index
                break
            position_index += 1
        
        '''
        -Tables with no compound keys will always have their PKs at position 0. 
            Hence, we ignore them.
        -There needs to be at least 2 PKs to create a compound key, therefore, 
            ignore any number below this position.
        -We will now loop again through the table to change the isPrimary to True, 
            based on the index found.
        '''
        if compound_end_point > 1:
            position_index = 0 #this will be used a limiter
            for field in fields_list:
                if position_index == compound_end_point:
                    break
                else:
                    field['isPrimary'] = True
                    position_index +=1
 
### MAIN PROGRAM ###

def generate(script_file):
    table_list = []
    # Read the script and gather the sql blocks
    blocks = read_script(script_file)
    # Process the gathered sql blocks
    process_sql_blocks(blocks, table_list)
    # Find compound keys and assign them
    assign_compound_keys(table_list)
    # Final output
    #print("Tables: " + json.dumps(table_list, indent=4, sort_keys=True) + "\n")
   # os.system('pause')
    return json.dumps(table_list, indent=4, sort_keys=True)