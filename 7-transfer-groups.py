import csv
import os
import requests
import logging
from requests.auth import HTTPBasicAuth
from config import cloud

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Define file paths directly
script_location = os.path.dirname(os.path.abspath(__file__))
membership_csv = os.path.join(script_location, "group-membership.csv")

workspace_id = cloud['workspace']

# Function to create group in Bitbucket Cloud
def create_group(workspace_id, group_name):
    try:
        response = requests.post(
            f"https://api.bitbucket.org/1.0/groups/{workspace_id}",
            auth=HTTPBasicAuth(cloud['username'], cloud['token']),  # Authentication setup
            data={"name": group_name}  # Data payload
        )
        return response
    except Exception as e:
        logging.exception(f"Failed to create group: {group_name}")
        return None

# Function to load group names from CSV and return a set of unique group names
def load_unique_groups(file_path):
    unique_groups = set()
    try:
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                unique_groups.add(row['group_name'])
    except Exception as e:
        logging.exception("Failed to load unique groups from CSV")
    return unique_groups

# Main function to create groups in Bitbucket Cloud
def create_groups_from_csv(workspace_id, membership_csv):
    unique_groups = load_unique_groups(membership_csv)
    for group_name in unique_groups:
        response = create_group(workspace_id, group_name)
        if response and response.ok:
            logging.info(f"Successfully created group: {group_name}")
        elif response:
            logging.error(f"Failed to create group: {group_name}, Reason: {response.text}")
        else:
            logging.error(f"Failed to create group: {group_name}, no response object.")

# Create groups from CSV file
create_groups_from_csv(workspace_id, membership_csv)
