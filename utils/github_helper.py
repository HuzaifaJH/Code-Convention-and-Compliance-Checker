import os
from dotenv import load_dotenv
import requests

load_dotenv()

# GitHub repository details
username = 'Farukh-Shaikh'
repository = 'Order-Management'
token = os.getenv('GITHUB_TOKEN')

base_dir = '../resources/github_files'

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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def process_directory(contents_url, current_dir):
    contents = get_repo_contents(contents_url)
    for content in contents:
        if content['type'] == 'file':
            file_content = get_file_content(content['url'])
            file_path = os.path.join(base_dir, current_dir, content['name'] + '.txt')
            save_file(file_path, file_content)
            print(f"Saved file: {file_path}")
        elif content['type'] == 'dir':
            new_dir = os.path.join(current_dir, content['name'])
            process_directory(content['url'], new_dir)

# URL to the repository contents
repo_url = f'https://api.github.com/repos/{username}/{repository}/contents'
