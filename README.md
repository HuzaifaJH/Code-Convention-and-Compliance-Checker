# Code-Convention-and-Compliance-Checker
Code Convention and Compliance Checker

# Step 1: install all libraries
pip install flask, openai, requests, python-dotenv

# Step 2:Setup .env file
Create .env file on root folder. Add these variables in the file

OPENAI_API_KEY = 'your open api key'
GITHUB_TOKEN = 'github token'
ASSISTANT_ID = 'gpt assistant id'
USERNAME = 'github username'
REPOSITORYNAME = 'github repo name'

# Step 3: Run pyhon server
python main.py
Utility will download all the files from the repo and upload on the OpenAI vector storage and connect that storage with GPT Assistant

# Step 4: Setup githook
Add CheckCodeConventions api url of this utility in git hook file in .net project







