import re
import json
import jsonschema
from jsonschema import validate


def fix_json(json_str):
    # Remove any trailing commas
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Attempt to fix unescaped quotes within strings
    json_str = re.sub(r'(?<!\\)"(?=(?:(?<!\\)(?:\\\\)*")*(?<!\\)(?:\\\\)*$)', r'\"', json_str)
    
    # Remove any non-printable characters
    json_str = ''.join(char for char in json_str if ord(char) > 31 or ord(char) == 9)
    json_str = json_str.replace('```', '').replace('\\', '')
    return json_str

# Function to validate the JSON output
def validate_json(json_output, json_schema):
    try:
        validate(instance=json_output, schema=json_schema)
        print("JSON is valid!")
    except jsonschema.exceptions.ValidationError as err:
        print("JSON is invalid!")
        print(err)


# Function to load a JSON file
def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)