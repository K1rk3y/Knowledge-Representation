from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import random

load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)

def selection(file_path, num, rng):
    with open(file_path, 'r') as file:
        data = json.load(file)

    if isinstance(data, list):
        if rng:
            objects = random.sample(data, min(num, len(data)))
            return objects
        else:
            objects = data[:10]
            return objects
    else:
        raise ValueError("JSON file does not contain a list of tuples or dictionaries.")
    

def comms(input, model="gpt-4o", max_tokens=2000, stop_sequence=None):
    messages=[
        {
            "role": "system",
            "content": "Normalize JSON object keys across multiple objects and mark keys as DEPRECATED if no no correspondence of said key can be found in other json objects. Return the updated json objects."
        },
        {
            "role": "user",
            "content": input
        }]

    try:
        response = client.chat.completions.create(
            messages=messages,
            response_format={ "type": "json_object" },
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
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
        objects = selection(file_path, 10, True)
    else:
        objects = selection(file_path, 10)

    for i, object in enumerate(objects):
        opt.appened(json_mode(comms(object)))

    return opt
