from requests.auth import HTTPBasicAuth
import csv
import json
import os
import requests
import logging
from config import cloud, on_prem

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Define file paths directly
script_location = os.path.dirname(os.path.abspath(__file__))
user_file = os.path.join(script_location, "bitbucket_users_match.csv") 
input_file = on_prem['bitbucket_server_repositories']

# Function to get server reviewer
def get_server_reviewer(project_key, repo_slug):
    try:
        response = requests.get(
            f"{on_prem['base_url']}/rest/default-reviewers/latest/projects/{project_key}/repos/{repo_slug}/conditions",
            auth=HTTPBasicAuth(on_prem['username'], on_prem['password']),  # Authentication setup
            headers={"Accept": "application/json"}  # Request headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch server reviewer for {repo_slug}: {response.text}")
            return []
    except Exception as e:
        logging.exception("Error fetching server reviewer")
        return []

# Function to add cloud reviewer
def add_cloud_reviewer(workspace, repo_slug, username):
    try:
        response = requests.request(
            "PUT",
            f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/default-reviewers/{username}",
            auth=HTTPBasicAuth(cloud['username'], cloud['token']),  # Authentication setup
            headers={"Accept": "application/json"}  # Request headers
        )
        return response
    except Exception as e:
        logging.exception(f"Error adding cloud reviewer for {repo_slug}")
        return None

# Main function to copy server reviewers to cloud
def copy_server_reviewers_to_cloud(project_key, repository_slug, workspace, user_map):
    reviewer_config_list = get_server_reviewer(project_key, repository_slug)
    for config in reviewer_config_list:
        for reviewer in config['reviewers']:
            key = str(reviewer['id'])
            if key not in user_map:
                logging.warning(f"Unable to add {reviewer['displayName']} to {repository_slug}, missing user on server.")
                continue

            user_data = user_map.get(key)
            if 'cloud_uuid' not in user_data:
                logging.warning(f"Unable to add {reviewer['displayName']} to {repository_slug}, missing user on cloud.")
                continue

            response = add_cloud_reviewer(workspace, repository_slug, user_data['cloud_uuid'])
            if response and response.ok:
                logging.info(f"{reviewer['displayName']} added to {repository_slug} ({response.status_code})")
            else:
                logging.error(f"Failed to add {reviewer['displayName']} to {repository_slug}. Error: {response.text if response else 'No response'}")

# Loading the user map from the CSV file
def load_user_map(user_file):
    user_map = {}
    with open(user_file) as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            user_map[row['server_id']] = row
    return user_map

# Load user map and process each repository from the input CSV
if __name__ == "__main__":
    user_map = load_user_map(user_file)
    with open(input_file) as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            logging.info(f"Copying server reviewers to cloud for project {row['project_key']} and repository {row['slug']}")
            copy_server_reviewers_to_cloud(row['project_key'], row['slug'], cloud['workspace'], user_map)
