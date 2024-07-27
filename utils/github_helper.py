import os
from dotenv import load_dotenv
import requests

load_dotenv()

# GitHub repository details
username = 'Farukh-Shaikh'
repository = 'Order-Management'
token = os.getenv('GITHUB_TOKEN')

repo_url = f'https://api.github.com/repos/{username}/{repository}/contents'

def get_repo_contents(repo_url):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(repo_url, headers=headers)
    return response.json()

def get_file_content(file_url):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    response = requests.get(file_url, headers=headers)
    return response.text

def save_file(file_path, content):
    # Print statements to debug path issues
    print(f"Saving file to: {file_path}")
    directory = os.path.dirname(file_path)
    print(f"Directory to create: {directory}")
    
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Write the file content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
        print(f"File saved successfully: {file_path}")


def process_directory(contents_url, dir):
    contents = get_repo_contents(contents_url)
    for content in contents:
        if content['type'] == 'file':
            # Remove extension from filename if it exists
            file_name = os.path.splitext(content['name'])[0] + '.txt'
            file_content = get_file_content(content['url'])
            file_path = os.path.join(dir, file_name).replace('\\', '/')
            save_file(file_path, file_content)
            print(f"Saved file: {file_path}")
        elif content['type'] == 'dir':
            # Continue processing recursively for directories
            process_directory(content['url'], dir)


# URL to the repository contents
# repo_url = f'https://api.github.com/repos/{username}/{repository}/contents'

# process_directory(repo_url)