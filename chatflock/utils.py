from typing import Any, Dict, Type

import re

from pydantic import BaseModel


def fix_invalid_json(json_string: str, only_cut: bool = False) -> str:
    # Cut anything before the first { and after the last }
    json_string = json_string[json_string.find("{") : json_string.rfind("}") + 1]

    if only_cut:
        return json_string

    # Regular expression patterns
    unquoted_key_pattern = r'(?<!")(\b\w+\b)(\s*:)(?!")'
    unquoted_value_pattern = r'(:\s*)([^",\]\[}{]+)(?=[,}\]])'

    # Fix unquoted keys
    json_string = re.sub(unquoted_key_pattern, r'"\1"\2', json_string)

    # Fix unquoted values by capturing until the next comma, closing brace, or bracket
    json_string = re.sub(unquoted_value_pattern, r'\1"\2"', json_string)

    # Handle string values with newlines and potential code
    string_field_pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    fixed_json = ""
    last_end = 0

    for m in re.finditer(string_field_pattern, json_string):
        start, end = m.span()
        string_value = m.group(1).replace("\n", "\\n")  # Fix newlines

        # Additional handling for strings that might contain code
        # Escaping quotes within the string value
        string_value = string_value.replace('"', '\\"')

        fixed_json += json_string[last_end:start] + '"' + string_value + '"'
        last_end = end

    fixed_json += json_string[last_end:]  # Add the remaining portion of the original string

    return fixed_json


def pydantic_to_json_schema(pydantic_model: Type[BaseModel]) -> Dict[str, Any]:
    try:
        return pydantic_model.model_json_schema()
    except AttributeError:
        return pydantic_model.schema()


def json_string_to_pydantic(json_string: str, pydantic_model: Type[BaseModel]) -> BaseModel:
    try:
        return pydantic_model.model_validate_json(json_string)
    except AttributeError:
        return pydantic_model.parse_raw(json_string)
