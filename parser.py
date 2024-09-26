from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import random


load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)


def selection(file_path, num, rng):
    objects = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                objects.append(data)
            except json.JSONDecodeError:
                continue
    
    if rng:
        return random.sample(objects, min(num, len(objects)))
    else:
        return objects[:num]


def comms(input, model="gpt-4o"):

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "Entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                "Entity": {
                    "type": ["string", "number"]
                },
                "Class": {
                    "type": "string",
                    "enum": ["Title", "Ancestor", "Guidid", "Category", "Tool", "ToolUrl", "ToolThumbnail", "Url", "Step", "StepLine", "StepImage", "StepId", "Subject"]
                }
                },
                "required": ["Entity", "Class"]
            }
            },
            "Relations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                "Source": {
                    "type": ["string", "number"]
                },
                "Target": {
                    "type": ["string", "number"]
                },
                "Relation": {
                    "type": "string",
                    "enum": ["hasAncestor", "hasGuidid", "hasCategory", "hasUrl", "hasThumbnail", "hasStepLine", "hasStepImage", "hasStepId", "hasSubject"]
                }
                },
                "required": ["Source", "Target", "Relation"]
            }
            }
        },
        "required": ["Entities", "Relations"]
    }

    messages=[
        {
            "role": "system",
            "content": f"Extract the entities, entity classes and relations in this json object based on this schema: {schema}"
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


def json_mode(raw):
    pass


def parse(file_path, test=True):
    objects = None
    opt = []
    if test:
        objects = selection(file_path, 1, False)
    else:
        objects = selection(file_path, 10, True)
    for i, object in enumerate(objects):
        opt.append(comms(object).replace('\n', ''))
    return opt

print(parse("PC.json", test=True))