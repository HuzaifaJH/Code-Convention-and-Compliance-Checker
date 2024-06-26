from flask import Flask, request, jsonify
import openai
import time
from utils import prompt_helper
import os
from dotenv import load_dotenv
import requests
import json
from utils.github_helper import process_directory

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
            git_diff = prompt_helper.preprocess_oneline_quotes(git_diff)
            git_diff = "New Code: "+git_diff
            # print(f"git_diff after preprocessing: {git_diff}")
            # Process the git_diff as needed
            
            thread = client.beta.threads.create()

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=git_diff
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

            cleaned_response = prompt_helper.clean_json_response(response)
            
            # Example response
            return jsonify(cleaned_response), 200
        else:
            return jsonify({'error': 'Invalid payload format'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/UploadVectorFile', methods=['POST'])
def UploadVectorFile():
    return

def upload_files_from_directory(vector_store_id, directory_path):
    files_uploaded = []
    
    # Fetch existing files in the vector store
    # existing_files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
    existing_files = client.files.list()
    existing_file_names = {file.filename: file for file in existing_files}
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        if os.path.isfile(file_path):
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
        process_directory(repo_url)
        directory_path = "./resources/github_files/"
        uploaded_files = upload_files_from_directory(vector_store_id, directory_path)
        print(f"Total files uploaded: {len(uploaded_files)}")
        print("Files Uploaded:")
        for file_info in uploaded_files:
            print(f"{file_info['filename']}: {file_info['upload_response']}")
        file_ids = [file_info['file_id'] for file_info in uploaded_files] # Extract file IDs from uploaded_files

        create_file_batch(vector_store_id, file_ids) # Example: Use the extracted file IDs to create a batch in a vector store
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

if __name__ == '__main__':
    
    #init()
    # Start the Flask app
    app.run()