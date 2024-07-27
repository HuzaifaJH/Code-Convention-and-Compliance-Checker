from flask import Flask, request, jsonify
import openai
import time
from utils import prompt_helper
import os
from dotenv import load_dotenv
import requests
import json
from utils.github_helper import process_directory
import urllib
import threading

load_dotenv()

app = Flask(__name__)

# Initialize OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
convention_assistant_id = "asst_OzMwQGIAMDEzV1YgHA2ARYVi"
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route('/api/CheckCodeConventions', methods=['POST'])
def check_code_conventions():
    try:
        # Assuming JSON payload: { "git_diff": "<git diff output>" }
        data = request.json  # Extract JSON data from the request body

        if 'git_diff' in data:
            git_diff = data['git_diff']
            filtered_lines = [line for line in git_diff.split('\n') if line.startswith('+') or line.startswith('-')]

            # Join the filtered lines back into a single string
            filtered_diff = '\n'.join(filtered_lines)
            git_diff = prompt_helper.preprocess_oneline_quotes(filtered_diff)
            git_diff = "New Code: "+git_diff
            # print(f"git_diff after preprocessing: {git_diff}")
            # Process the git_diff as needed
            
            thread_id = 'thread_c1s66lEfkm7sqCgNkVlGsyDf'
            # thread = client.beta.threads.create()

            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=git_diff
            )

            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=convention_assistant_id
            )

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                print(f"Run Status: {run.status}")
                time.sleep(0.5)
            else:
                print(f"Run Completed")

            messages_response = client.beta.threads.messages.list(thread_id=thread_id)
            response = messages_response.data[0].content[0].text.value

            print(f"Response: {response}")

            cleaned_response = prompt_helper.clean_json_response(response)
            
            for item in cleaned_response['Explanation']:
                if item['Score'] > 7:
                    cleaned_response['Validation'] = False
                    break
                elif item['Score'] != 0 and item['Score'] < 7:
                    cleaned_response ['Validation'] = True

            # Example response
            return jsonify(cleaned_response), 200
        else:
            return jsonify({'error': 'Invalid payload format'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/UploadVectorFile', methods=['POST'])
def UploadVectorFile():
    return

def upload_files_from_directory(directory_path):
    files_uploaded = []
    
    # Fetch existing files in the vector store
    # existing_files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
    existing_files = client.files.list()
    existing_file_names = {file.filename: file for file in existing_files}
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        if os.path.isfile(file_path):
            if "pre-commit" in filename:
                print(f"Skipping file: {filename} (contains 'pre-commit')")
                continue

            try:
                # Check if the file already exists in the vector store
                if filename in existing_file_names:
                    existing_file = existing_file_names[filename]
                    # Delete the existing file
                    client.files.delete(file_id=existing_file.id)
                    print(f"Deleted existing file: {filename} ({existing_file.id})")

                # Upload file to OpenAI
                upload_response = client.files.create(
                    file=open(file_path, "rb"),
                    purpose='assistants',
                )
                files_uploaded.append({
                    'filename': filename,
                    'file_id': upload_response.id,
                    'upload_response': upload_response
                })
                print(f"Uploaded {filename} successfully. File ID: {upload_response.id}")
                
            except openai.error.OpenAIError as e:
                print(f"Failed to upload {filename}: {e}")
    
    return files_uploaded

def create_file_batch(vector_store_id, file_ids):
    batch_add = client.beta.vector_stores.file_batches.create(
        vector_store_id=vector_store_id,
        file_ids=file_ids
    )
    print(f"Batch creation initiated. Batch ID: {batch_add.id}")
    
    # Monitor batch status until it's not in_progress
    while batch_add.status == 'in_progress':
        time.sleep(1)
        batch_add = client.beta.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            batch_id=batch_add.id
        )
        print(f"Current status: {batch_add.status}")
    
    print(f"Batch creation status: {batch_add.status}")

def init():
    # GitHub processing
    owner = 'Farukh-Shaikh'
    repo = 'Order-Management'
    repo_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    
    
    vector_store_id = 'vs_FEaAVUV1u1j9AOFWb2mKC9a9'

    try:
        base_dir = './resources/github_files'
        process_directory(repo_url, base_dir)
        directory_path = "./resources/github_files/"
        uploaded_files = upload_files_from_directory(directory_path)
        print(f"Total files uploaded: {len(uploaded_files)}")
        print("Files Uploaded:")
        for file_info in uploaded_files:
            print(f"{file_info['filename']}: {file_info['upload_response']}")
        file_ids = [file_info['file_id'] for file_info in uploaded_files] # Extract file IDs from uploaded_files

        create_file_batch(vector_store_id, file_ids) # Example: Use the extracted file IDs to create a batch in a vector store
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

def compliance_check_thread():
    owner = 'Farukh-Shaikh'
    repo = 'Order-Management'
    branch = 'main'
    repo_url = f'https://api.github.com/repos/{owner}/{repo}/contents?ref={branch}'
    
    vector_store_id = 'vs_Cz9bNSFYeMJJ00Qzk6AhDfCj'

    try:
        compliance_dir = './compliance/github_files'
        process_directory(repo_url, compliance_dir)
        directory_path = "./compliance/github_files/"
        uploaded_files = upload_files_from_directory(directory_path)
        print(f"Total files uploaded: {len(uploaded_files)}")
        print("Files Uploaded:")
        for file_info in uploaded_files:
            print(f"{file_info['filename']}: {file_info['upload_response']}")
        file_ids = [file_info['file_id'] for file_info in uploaded_files]  # Extract file IDs from uploaded_files

        create_file_batch(vector_store_id, file_ids)  # Example: Use the extracted file IDs to create a batch in a vector store

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Analyze the code provided in Vector storage"
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_Dnsfxy9nncLHVDNHFnvYfcPU"
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

        subject = "Compliance and Code Conventions Check - Action Required"
        body = f"""
        Dear Lead,

        I hope this message finds you well.

        I am writing to inform you that our recent compliance check identified some issues that need attention.

        Summary of Issues Identified:

        {response}

        Please find the results attached for your review. Prompt attention to these matters will ensure that our project meets the required standards and regulations.

        Regards,
        C4
        """

        send_email(subject, body)

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

@app.route('/api/checkCompliance', methods=['GET'])
def check_compliance():
    # Start the compliance check in a new thread
    threading.Thread(target=compliance_check_thread).start()
    
    # Return a 200 response immediately
    return jsonify({"message": "Compliance check started"}), 200
def send_email(subject, body):
    receiver = "juzerhuzaifa@gmail.com"
    scriptUrl = "https://script.google.com/macros/s/AKfycby_wG3HbEPgE9uRk-WAp2JoyCQN4_zC6_TQGANDJF2zdzaN1jIyn1_ybHv7RJigENvo/exec"
 
    query_params = { 'email': receiver, 'title': subject, 'body': body}
    encoded_params = urllib.parse.urlencode(query_params)
    scriptUrl = scriptUrl + "?" + encoded_params
 
    try:
        response = requests.get(scriptUrl)
 
        if response.status_code == 200:
            print("Success:", response.text)
        else:
            print("Failed with status code:", response.status_code)
            print("Response:", response.text)
 
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == '__main__':
    
    init()
    # Start the Flask app
    app.run()