import csv
import requests
import os
import logging
from requests.auth import HTTPBasicAuth
from config import cloud

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define file paths directly
script_location = os.path.dirname(os.path.abspath(__file__))
users_file = os.path.join(script_location, "bitbucket_users_match.csv")
membership_csv = os.path.join(script_location, "group-membership.csv")

# Read the 'bitbucket_users_match.csv' and create a mapping from display_name to cloud_uuid
def create_displayname_to_uuid_map(users_file):
    displayname_to_uuid_map = {}
    try:
        with open(users_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                display_name = row['cloud_display_name']
                cloud_uuid = row['cloud_uuid']
                displayname_to_uuid_map[display_name] = cloud_uuid
    except Exception as e:
        logging.error(f"Error reading users file {users_file}: {e}")
    return displayname_to_uuid_map

# Get group slugs from Bitbucket API
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
            logging.error(f"Failed to fetch group slugs. Response: {response.text}")
    except Exception as e:
        logging.error(f"Exception occurred while fetching group slugs: {e}")
    return group_slugs

# Function to add a user to a group in Bitbucket Cloud
def add_user_to_group(workspace_id, group_slug, user_uuid):
    try:
        response = requests.put(
            f"https://api.bitbucket.org/1.0/groups/{workspace_id}/{group_slug}/members/{user_uuid}/",
            auth=HTTPBasicAuth(cloud['username'], cloud['token']),  # Authentication setup
            data='{}'  # Empty data payload as per the API requirement
        )
        if response.ok:
            logging.info(f"Successfully added user {user_uuid} to group {group_slug}")
        else:
            logging.warning(f"Failed to add user {user_uuid} to group {group_slug}. Response: {response.text}")
    except Exception as e:
        logging.error(f"Exception occurred while adding user to group: {e}")

# Main function to add users to groups based on the CSV files
def add_users_to_groups(workspace_id, users_file, membership_csv, group_slugs):
    # Create the mapping from display names to UUIDs
    displayname_to_uuid_map = create_displayname_to_uuid_map(users_file)
    
    try:
        with open(membership_csv, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                display_name = row['display_name']
                group_name = row['group_name']
                group_slug = group_slugs.get(group_name)
                user_uuid = displayname_to_uuid_map.get(display_name)
                
                if group_slug and user_uuid:
                    add_user_to_group(workspace_id, group_slug, user_uuid)
                    logging.info(f"{display_name} added to group {group_slug}")
                else:
                    logging.warning(f"Missing group slug or user UUID for {display_name} in group {group_name}.")
    except Exception as e:
        logging.error(f"Error processing membership CSV: {e}")

workspace_id = cloud['workspace'] 
group_slugs = get_group_slugs(workspace_id)
add_users_to_groups(workspace_id, users_file, membership_csv, group_slugs)
