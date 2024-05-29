import csv
import requests
import json
import os
import subprocess
import urllib.parse
import logging
from requests.auth import HTTPBasicAuth
from config import cloud, on_prem, project_key, repository_folder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

should_sync_lfs = True

def run_command(command, cwd=None):
    """Execute a system command with optional working directory."""
    logging.info(f"Executing: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, check=True)
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with error: {e.stderr}")

def get_uuid_from_display_name(display_name):
    """Retrieve UUID for a given display name from a CSV file."""
    filepath = os.path.join(os.path.dirname(__file__), 'bitbucket_users_match.csv')
    with open(filepath, mode='r') as csvfile:
        for row in csv.DictReader(csvfile):
            if row['server_displayName'] == display_name:
                return row['cloud_uuid']
    return None

def set_admin_permission(repo_slug, uuid):
    """Sets admin permission for the provided UUID on the created repository."""
    logging.info(f"Setting admin permission for {uuid} on repository {repo_slug}...")
    url = f"https://api.bitbucket.org/2.0/workspaces/{cloud['workspace']}/projects/{project_key}/permissions-config/users/{uuid}"
    payload = {"permission": "admin"}
    response = requests.put(url, auth=HTTPBasicAuth(cloud['username'], cloud['token']), headers={"Content-Type": "application/json"}, json=payload)
    
    if response.ok:
        logging.info(f"Admin permission successfully set for {uuid} on repository {repo_slug}.")
    else:
        logging.error(f"Error setting admin permission for {uuid} on repository {repo_slug}: {response.text}")

def create_cloud_repo(source_url, repo_name, uuid, username):
    """Creates a repository on Bitbucket Cloud using the user's UUID, sets the admin and clone and sync the repo"""
    logging.info(f"Creating repository '{repo_name}' on Bitbucket Cloud...")
    new_repo_name = f"{username}-{repo_name}"
    url = f"https://api.bitbucket.org/2.0/repositories/{cloud['workspace']}/{new_repo_name}"
    payload = {"scm": "git", "is_private": True, "project": {"key": project_key}, "owner": {"type": uuid}}
    
    response = requests.post(url, auth=HTTPBasicAuth(cloud['username'], cloud['token']), headers={"Content-Type": "application/json"}, json=payload)
    if response.ok:
        logging.info(f"Repository '{repo_name}' successfully created on Bitbucket Cloud.")
        set_admin_permission(new_repo_name, uuid)
        clone_and_sync_repos(source_url, response.json()['links']['clone'][0]['href'], new_repo_name)
    else:
        logging.error(f"Error creating repository '{repo_name}': {response.text}")

def clone_and_sync_repos(source_url, target_url, new_repo_name):
    """Clones and syncs repositories, including LFS files if enabled."""
    logging.info(f"\nProcessing [{new_repo_name}] repository...")
    credentials = f"{on_prem['username']}:{urllib.parse.quote_plus(on_prem['password'])}"
    source_url_with_credentials = source_url.replace('https://', f"https://{credentials}@").replace('http://', f"http://{credentials}@")
    repo_folder = os.path.join(repository_folder, new_repo_name)
    
    if not os.path.exists(repo_folder):
        run_command(f"git clone {source_url_with_credentials} \"{repo_folder}\"")
        run_command(f"git remote add cloud {target_url}", cwd=repo_folder)
        run_command(f"git push cloud master", cwd=repo_folder)
    else:
        logging.info("Repository already exists, skipping clone.")
    
    if should_sync_lfs:
        run_command("git lfs fetch --all", cwd=repo_folder)
        run_command("git lfs push --all cloud", cwd=repo_folder)

def process_repos():
    """Processes repositories from CSV, creating them on Bitbucket Cloud with admin permissions."""
    logging.info("Starting repository processing...")
    filepath = os.path.join(os.path.dirname(__file__), "personal-repos.csv")
    with open(filepath, mode='r') as csvfile:
        for row in csv.DictReader(csvfile):
            logging.info(f"Processing repository for user: {row['User']}")
            username, repo_slug = row['User'], row['Repository Slug']
            server_url = f"{on_prem['base_url']}/rest/api/1.0/projects/{username}/repos/{repo_slug}"
            response = requests.get(server_url, auth=HTTPBasicAuth(on_prem['username'], on_prem['password']))
            
            if response.ok:
                repo_details = response.json()
                display_name = repo_details['project']['owner']['displayName']
                source_clone = repo_details['links']['clone'][0]['href']
                uuid = get_uuid_from_display_name(display_name)
                if uuid:
                    create_cloud_repo(source_clone, repo_slug, uuid, username.strip("~"))
                else:
                    logging.warning(f"UUID not found for displayName: {display_name}")
            else:
                logging.error(f"Error fetching repository details '{repo_slug}' from the server: {response.text}")

if __name__ == "__main__":
    process_repos()
