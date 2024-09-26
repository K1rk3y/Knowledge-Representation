from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import random
from typing import Set, Any, Dict, List


load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)


def selection(file_path, num):
    objects = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                objects.append(data)
            except json.JSONDecodeError:
                continue
    
    return objects[:num]


def comms(input, model="gpt-4o"):
    messages=[
        {
            "role": "system",
            "content": "List the RDF entity classes and relations in this json object."
        },
        {
            "role": "user",
            "content": json.dumps(input)
        }]
    try:
        response = client.chat.completions.create(
            messages=messages,
            response_format={ "type": "json_object" },
            temperature=0,
            top_p=0,
            model=model
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return ""


def parse_json(json_obj: dict, string_list: List[str]) -> tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    top_level_keys = set()
    nested_keys = set()

    def process_nested(obj: Any, prefix: str = ""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f"{prefix}-{key}" if prefix else key
                nested_keys.add(new_prefix)
                process_nested(value, new_prefix)
        elif isinstance(obj, list):
            for item in obj:
                process_nested(item, prefix)

    def extract_string(term):
        prefix = "has"
        if term.startswith(prefix):
            return term[len(prefix):]
        return term

    for key, value in json_obj.items():
        top_level_keys.add(key)
        process_nested(value, key)

    def match_substrings(key: str) -> List[str]:
        return [s for s in string_list if any(part.lower() in extract_string(s).lower() or part.lower()[:-1] in extract_string(s).lower() for part in key.split('-'))]

    top_level_dict = {key: match_substrings(key) for key in top_level_keys}
    nested_dict = {key for key in nested_keys}

    return top_level_dict, nested_dict


def parse(file_path):
    objects = None
    opt = []
    string_list = ["hasAncestor", "hasGuidid", "hasCategory", "hasUrl", "hasThumbnail", "hasStepLine", "hasStepImage", "hasStepId", "hasTitle", "hasTool, hasSubject"]
  
    objects = selection(file_path, 1)
 
    for object in objects:
        top, nested = parse_json(object, string_list)
        opt.append(top)
        opt.append(nested)

    return opt

print(parse("TEST.json"))