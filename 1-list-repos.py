import csv
import json
import os
import requests
import logging
from requests.auth import HTTPBasicAuth
from config import cloud, on_prem

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_bitbucket_cloud_repos(workspace, username, token, output_file):
    logging.info("Starting to fetch Bitbucket Cloud repositories.")
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    auth = HTTPBasicAuth(username, token)
    headers = {"Accept": "application/json"}

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['uuid', 'slug', 'name', 'scm', 'https', 'ssh'])

            while url:
                response = requests.get(url, auth=auth, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get('values', []):
                        clone_https = repo['links']['clone'][0]['href']
                        clone_ssh = repo['links']['clone'][1]['href']
                        writer.writerow([repo['uuid'], repo['slug'], repo['name'], repo['scm'], clone_https, clone_ssh])
                    url = data.get('next', None)
                else:
                    logging.error(f"Failed to fetch repositories: {response.text}")
                    break
        logging.info("Successfully fetched and saved Bitbucket Cloud repositories.")
    except Exception as e:
        logging.error(f"Error fetching Bitbucket Cloud repositories: {e}")

def get_bitbucket_server_repos(base_url, username, password, output_file):
    logging.info("Starting to fetch Bitbucket Server repositories.")
    auth = HTTPBasicAuth(username, password)  # Authentication setup
    headers = {"Accept": "application/json"}  # Request headers
    project_limit = 100  # Define the project limit
    repo_limit = 1000  # Define the repository limit

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'slug', 'name', 'scmId', 'project_key', 'https', 'ssh'])  # Header row for CSV

            # Pagination setup for projects
            projects_start = 0
            projects_is_last_page = False

            while not projects_is_last_page:
                projects_url = f"{base_url}/rest/api/1.0/projects?start={projects_start}&limit={project_limit}"
                projects_response = requests.get(projects_url, auth=auth, headers=headers)
                if projects_response.status_code == 200:
                    projects_data = projects_response.json()
                    projects = projects_data.get('values', [])
                    projects_is_last_page = projects_data.get('isLastPage', True)

                    for project in projects:
                        # Logging each project being processed
                        logging.info(f"Processing project: {project['key']}")
                        repos_start = 0
                        repos_is_last_page = False

                        while not repos_is_last_page:
                            repos_url = f"{base_url}/rest/api/1.0/projects/{project['key']}/repos?start={repos_start}&limit={repo_limit}"
                            repos_response = requests.get(repos_url, auth=auth, headers=headers)
                            if repos_response.status_code == 200:
                                repos_data = repos_response.json()
                                repos = repos_data.get('values', [])
                                repos_is_last_page = repos_data.get('isLastPage', True)

                                for repo in repos:
                                    clone_https = None
                                    clone_ssh = None
                                    for clone_link in repo['links']['clone']:
                                        if clone_link['name'] == 'http':
                                            clone_https = clone_link['href']
                                        elif clone_link['name'] == 'ssh':
                                            clone_ssh = clone_link['href']
                                    if clone_https or clone_ssh:
                                        writer.writerow([repo['id'], repo['slug'], repo['name'], repo['scmId'], project['key'], clone_https, clone_ssh])
                                        logging.info(f"Added repository '{repo['name']}' to CSV.")
                            else:
                                logging.error(f"Failed to fetch repositories for project {project['key']}. Status code: {repos_response.status_code}")
                                break

                        if not projects_is_last_page:
                            projects_start += project_limit
                else:
                    logging.error(f"Failed to fetch projects. Status code: {projects_response.status_code}")
                    break
            logging.info("Successfully fetched and saved Bitbucket Server repositories.")
    except Exception as e:
        logging.error(f"Error while fetching Bitbucket Server repositories: {e}")


def merge_repos_to_csv(server_csv, cloud_csv, output_csv):
    """Merges data from Bitbucket Server and Cloud CSV files into a single CSV file."""
    try:
        script_dir = os.path.dirname(__file__)
        server_csv_path = os.path.join(script_dir, server_csv)
        cloud_csv_path = os.path.join(script_dir, cloud_csv)
        
        server_repos = {}
        with open(server_csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                server_repos[row['name']] = row

        cloud_repos = {}
        with open(cloud_csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cloud_repos[row['name']] = row

        with open(output_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'project', 'match', 'source', 'target'])

            for name, server_repo in server_repos.items():
                if name in cloud_repos:
                    cloud_repo = cloud_repos[name]
                    project = server_repo['project_key']
                    match = "yes"
                    source = server_repo['https']
                    target = cloud_repo['https']
                    writer.writerow([name, project, match, source, target])
        logging.info("Successfully merged repositories into a single CSV.")
    except Exception as e:
        logging.error(f"Error merging repositories: {e}")

# Fetch and merge repositories
get_bitbucket_cloud_repos(cloud['workspace'], cloud['username'], cloud['token'], cloud['bitbucket_cloud_repositories'])
get_bitbucket_server_repos(on_prem['base_url'], on_prem['username'], on_prem['password'], on_prem['bitbucket_server_repositories'])
merge_repos_to_csv(on_prem['bitbucket_server_repositories'], cloud['bitbucket_cloud_repositories'], 'merged_repositories.csv')
