from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from collections import Counter
from typing import Any, Dict, List


""" load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key) """


""" def extract_hazards(input, model="gpt-4o"):
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
        return "" """


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


def extract_classes(json_obj: dict, string_list: List[str]) -> tuple[Dict[str, List[str]], Dict[str, List[str]]]:
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
        
    def partition(s: str, n: int) -> List[str]:
        s = s.lower()
        return [s[i:i+n] for i in range(len(s) - n + 1)]

    def ngram_similarity(key: str, s: str, n: int) -> float:
        key_ngrams = partition(key, n)
        s_ngrams = partition(s, n)

        key_counter = Counter(key_ngrams)
        s_counter = Counter(s_ngrams)

        common_ngrams = sum((key_counter & s_counter).values())
        total_ngrams = sum(key_counter.values())

        if total_ngrams == 0:
            return 0.0

        return common_ngrams / total_ngrams

    def match_substrings(key: str, string_list: List[str], n: int = 3, threshold: float = 0.3) -> List[str]:
        matched_strings = []
        for s in string_list:
            similarity = ngram_similarity(key, s, n)
            if similarity >= threshold:
                matched_strings.append(s)
        
        return matched_strings

    for key, value in json_obj.items():
        top_level_keys.add(key)
        process_nested(value, key)

    top_level_dict = {key: match_substrings(key, string_list) for key in top_level_keys}
    nested_dict = {key for key in nested_keys}

    return top_level_dict, nested_dict


def process_nested(obj: Any, prefix: str = "", nested_keys=None):
    if nested_keys is None:
        nested_keys = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}-{key}" if prefix else key
            nested_keys.add(new_prefix)
            process_nested(value, new_prefix, nested_keys)
    elif isinstance(obj, list):
        for item in obj:
            process_nested(item, prefix, nested_keys)

    return nested_keys


def extract_entities(json_obj, parent_id=None):
    result = []

    def process_layer(layer, parent_id=None, parent_key_prefix=""):
        extracted_layer = {}
        nested_keys = []

        # Check if there's an "id" key in the current layer
        layer_id = None
        for key, value in layer.items():
            if "id" in key.lower():
                layer_id = value
                break

        # If no ID key in the current layer, use parent ID
        if layer_id is None and parent_id:
            layer_id = parent_id

        for key, value in layer.items():
            # Prepend parent keys to current key using the prefix
            full_key = f"{parent_key_prefix}-{key}" if parent_key_prefix else key

            if isinstance(value, list) and all(isinstance(i, dict) for i in value):
                # Mark nested lists as "NESTED" and track them for recursion
                extracted_layer[f"{full_key}_{layer_id}"] = "NESTED"
                nested_keys.append((full_key, value))
            else:
                extracted_layer[f"{full_key}_{layer_id}"] = value

        result.append(extracted_layer)

        for full_key, nested_value in nested_keys:
            for nested_layer in nested_value:
                process_layer(nested_layer, layer_id, full_key)

    process_layer(json_obj, parent_id)
    return result


def parse(file_path):
    objects = None
    entity_relations = []
    values = []
    string_list = ["hasAncestor", "hasGuidid", "hasCategory", "hasUrl", "hasThumbnail", "hasStepLine", "hasStepImage", "hasStepId", "hasTitle", "hasTool", "hasSubject"]
  
    objects = selection(file_path, 1)
 
    for object in objects:
        top, nested = extract_classes(object, string_list)
        entities = extract_entities(object)

        entity_relations.append(top)
        entity_relations.append(nested)
        values.append(entities)

    return entity_relations, values


print(parse("TEST.json"))
