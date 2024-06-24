from flask import Flask, request, jsonify
import openai
import time
from utils import prompt_helper
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

# Initialize OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
convention_assistant_id = "asst_OzMwQGIAMDEzV1YgHA2ARYVi"
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route('/api/CheckCodeConventions', methods=['POST'])
def CheckCodeConventions():
    prompt_text = prompt_helper.read_prompt_from_file(os.path.abspath("resources/prompt.txt"))

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=convention_assistant_id
    )

    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(f"Run Status: {run.status}")
        time.sleep(0.5)
    else:
        print(f"Run Completed")

    messages_response = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages_response.data[0].content[0].text.value

    print(f"Response: {response}")

    return prompt_helper.clean_json_response(response)

@app.route('/api/UploadVectorFile', methods=['POST'])
def UploadVectorFile():
    return

if __name__ == '__main__':
    app.run(debug=True)
