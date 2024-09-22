import ast
import json


def parse_json_output(output):
    if output.startswith("```json"):
        output = output[8:]
    if output.endswith("```"):
        output = output[:-3]
    try:
        return json.loads(output)
    except Exception as e:
        try:
            return ast.literal_eval(output)
        except Exception as e:
            return output
