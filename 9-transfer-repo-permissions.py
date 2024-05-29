import csv
import requests
import os
import logging
from requests.auth import HTTPBasicAuth
from config import cloud, on_prem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def which_project_permission(permission):
    return {
        "PROJECT_WRITE": "write",
        "PROJECT_READ": "read",
        "PROJECT_ADMIN": "admin",
    }.get(permission, "")
    
def which_repo_permission(permission):
    return {
        "REPO_WRITE": "write",
        "REPO_READ": "read",
        "REPO_ADMIN": "admin",
    }.get(permission, "")

def get_group_slugs(workspace_id):
    url = f"https://api.bitbucket.org/1.0/groups/{workspace_id}/"
    auth = HTTPBasicAuth(cloud['username'], cloud['token'])
    try:
        response = requests.get(url, auth=auth)
        group_slugs = {}
        if response.ok:
            for group in response.json():
                group_slugs[group['name']] = group['slug']
            logging.info(f"Retrieved group slugs for workspace: {workspace_id}")
        else:
            logging.error(f"Failed to retrieve group slugs for workspace: {workspace_id}. Status code: {response.status_code}")
        return group_slugs
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving group slugs: {e}")
        return {}

script_location = os.path.dirname(os.path.abspath(__file__))
bitbucket_server_repositories = os.path.join(script_location, on_prem["bitbucket_server_repositories"]) 

logging.info("Fetching group slugs from Bitbucket API...")
group_slugs = get_group_slugs(cloud['workspace'])

def get_uuid_from_user(displayName):
    users_file = os.path.join(script_location, "bitbucket_users_match.csv")  
    with open(users_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row['cloud_display_name'] == displayName:
                return row['cloud_uuid'] 
    return None 

project_keys_set = set()
with open(bitbucket_server_repositories, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        project_keys_set.add(row['project_key'])

logging.info("Processing project permissions...")
for project_key in project_keys_set:

    users_response = requests.get(
        f"{on_prem['base_url']}/rest/api/1.0/projects/{project_key}/permissions/users",
        auth = HTTPBasicAuth(on_prem['username'], on_prem['password']), 
        headers = {"Accept": "application/json"}  # Request headers
    ).json()
    
    for user in users_response['values']:
        mapped_permission = which_project_permission(user['permission'])
        if mapped_permission:
            
            user_uuid = get_uuid_from_user(user['user']['displayName'])
            
            if user_uuid != '': 
            
                response = requests.request(
                    'PUT',
                    f"https://api.bitbucket.org/2.0/workspaces/{cloud['workspace']}/projects/{project_key}/permissions-config/users/{user_uuid}",
                    auth = HTTPBasicAuth(cloud['username'], cloud['token']), 
                    headers = {"Accept": "application/json"},
                    json={"permission": mapped_permission}
                )
            
    groups_response = requests.get(
        f"{on_prem['base_url']}/rest/api/1.0/projects/{project_key}/permissions/groups",
        auth = HTTPBasicAuth(on_prem['username'], on_prem['password']), 
        headers = {"Accept": "application/json"}
    ).json()

    for group in groups_response['values']:
        mapped_permission = which_project_permission(group['permission'])
        if mapped_permission:
            
            group_slug = group_slugs.get(group['group']['name'])
            
            if group_slug != '': 
            
                response = requests.request(
                    'PUT',
                    f"https://api.bitbucket.org/2.0/workspaces/{cloud['workspace']}/projects/{project_key}/permissions-config/groups/{group_slug}",
                    auth = HTTPBasicAuth(cloud['username'], cloud['token']), 
                    headers = {"Accept": "application/json"},
                    data={"permission": mapped_permission}
                )
                
    logging.info(f"Processed permissions for project: {project_key}")    
    
#repo level     
logging.info("Processing repository permissions...")           
with open(bitbucket_server_repositories, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        
        repo_slug = row['slug']
        project_key = row['project_key']

        users_response = requests.get(
            f"{on_prem['base_url']}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/permissions/users",
            auth = HTTPBasicAuth(on_prem['username'], on_prem['password']), 
            headers = {"Accept": "application/json"}  # Request headers
        ).json()
        
        for user in users_response['values']:
            mapped_permission = which_project_permission(user['permission'])
            if mapped_permission:
                
                user_uuid = get_uuid_from_user(user['user']['displayName'])
                
                if user_uuid != '': 
                
                    response = requests.request(
                        'PUT',
                        f"https://api.bitbucket.org/2.0/repositories/{cloud['workspace']}/{repo_slug}/permissions-config/users/{user_uuid}",
                        auth = HTTPBasicAuth(cloud['username'], cloud['token']), 
                        headers = {"Accept": "application/json"},
                        json={"permission": mapped_permission}
                    )
                
        groups_response = requests.get(
            f"{on_prem['base_url']}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/permissions/groups",
            auth = HTTPBasicAuth(on_prem['username'], on_prem['password']), 
            headers = {"Accept": "application/json"}
        ).json()

        for group in groups_response['values']:
            mapped_permission = which_project_permission(group['permission'])
            if mapped_permission:
                
                group_slug = group_slugs.get(group['group']['name'])
                
                if group_slug != '': 
                
                    response = requests.request(
                        'PUT',
                        f"https://api.bitbucket.org/2.0/repositories/{cloud['workspace']}/{repo_slug}/permissions-config/groups/{group_slug}",
                        auth = HTTPBasicAuth(cloud['username'], cloud['token']), 
                        headers = {"Accept": "application/json"},
                        data={"permission": mapped_permission}
                    )
                    
    logging.info(f"Processed permissions for repository: {repo_slug}")    
                    
logging.info("Permissions processing complete.")
