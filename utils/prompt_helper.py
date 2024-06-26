import re
import json

def preprocess_oneline_quotes(prompt):
    prompt = re.sub(r"\r?\n|\r", " ", prompt)  # makes all in one line
    return prompt.replace('"', '\\"')  # escape quotation marks


def read_prompt_from_file(filePath):
    try:
        with open(filePath, "r") as file:
            return preprocess_oneline_quotes(file.read())
    except Exception as e:
        print(f"An error occurred: {e}")


def clean_json_response(resp):
    resp = resp.replace('```json', '')
    resp = resp.replace('```' , '')
    resp = resp.replace('\n', '')
    resp = resp.replace('\xa0', '')
    return json.loads(resp)
