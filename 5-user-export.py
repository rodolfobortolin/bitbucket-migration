from requests.auth import HTTPBasicAuth
import csv
import os
import requests
from unidecode import unidecode
from config import cloud, on_prem

def merge_csv_rows_in_place(csv_path):
    """
    Merges rows in a CSV file based on matching server_slug or cloud_nickname, modifying the file in place.

    Parameters:
    - csv_path: Path to the CSV file to be modified.
    """
    # Read the input CSV file into a list of dictionaries
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]

    # Merge rows with the same server_slug or cloud_nickname
    merged_rows = {}
    for row in rows:
        key = row['server_slug'] if row['server_slug'] else row['cloud_nickname']
        if key in merged_rows:
            # Merge values, preferring non-empty values
            for field in row:
                if row[field]:  # If the current row's field is not empty
                    merged_rows[key][field] = row[field]  # Update the merged row's field
        else:
            merged_rows[key] = row

    # Overwrite the original CSV file with merged rows
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = rows[0].keys()  # Assuming all rows have the same fields
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_rows.values():
            writer.writerow(row)

    print(f'The CSV file {csv_path} has been modified in place with merged rows.')


# Function to normalize keys
def hash_key(value):
    return unidecode(value.lower())

# Function to get cloud users
def get_cloud_users(workspace):
    
    auth = HTTPBasicAuth(cloud['username'], cloud['token']) 
    headers = {"Accept": "application/json"} 
    
    response = requests.get(
        f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members?pagelen=100", 
        auth=auth, 
        headers=headers)
    
    return response.json()['values']

# Function to get server users
def get_server_users():
    
    auth = HTTPBasicAuth(on_prem['username'], on_prem['password']) 
    headers = {"Accept": "application/json"}
    
    response = requests.get(
        f"{on_prem['base_url']}/rest/api/latest/users?limit=3000",
        auth=auth,
        headers=headers
    )
    
    return response.json()['values']

# Main process
def main():
    user_map = {}
    cloud_user_names = set()
    server_user_names = set()

    script_location = os.path.dirname(os.path.abspath(__file__))
    default_output_file = os.path.join(script_location, "bitbucket_users_match.csv") 

    # Processing cloud users
    for user in get_cloud_users(cloud['workspace']):
        key = hash_key(user['user']['display_name'])
        cloud_user_names.add(key)
        user_map[key] = {
            'cloud_account_id': user['user']['account_id'],
            'cloud_uuid': user['user']['uuid'],
            'cloud_nickname': user['user']['nickname'],
            'cloud_display_name': user['user']['display_name'],
        }

    # Processing server users
    for user in get_server_users():
        key = hash_key(user['displayName'])
        server_user_names.add(key)
        if key not in user_map:
            user_map[key] = {}
        user_map[key].update({
            'server_id': user['id'],
            'server_slug': user['slug'],
            'server_displayName': user['displayName'],
            'server_emailAddress': user['emailAddress']
        })

    with open(default_output_file, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        headers = ['server_slug', 'server_id', 'server_displayName', 'server_emailAddress', 'cloud_uuid', 'cloud_account_id', 'cloud_nickname', 'cloud_display_name']
        writer.writerow(headers)
        for user in user_map.values():
            writer.writerow([
                user.get('server_slug'),
                user.get('server_id'),
                user.get('server_displayName'),
                user.get('cloud_uuid'),
                user.get('cloud_account_id'),
                user.get('cloud_nickname'),
                user.get('cloud_display_name'),
            ])
            
    merge_csv_rows_in_place(default_output_file)

if __name__ == "__main__":
    main()
