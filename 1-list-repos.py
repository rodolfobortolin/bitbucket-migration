import csv
import os
import subprocess
import urllib.parse
import logging
from config import on_prem, repository_folder

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Determine the path to the 'repositories' subfolder relative to this script's location
script_location = os.path.dirname(os.path.abspath(__file__))
save_folder = os.path.join(script_location, repository_folder)

# Ensure the 'repositories' subfolder exists
os.makedirs(save_folder, exist_ok=True)

# Predefined configuration variables
input_csv = os.path.join(script_location, "merged_repositories.csv")  # Adjusted for script location
should_clone = True  # Set to True to clone repositories
should_sync_lfs = True  # Set to True to sync LFS files

def run_command(command, cwd=None):
    """Execute a system command with optional working directory."""
    logging.info(f"Executing: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.stdout:
            logging.debug(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
    except Exception as e:
        logging.exception("Failed to execute command")

def clone_and_sync_repos():
    """Clone and sync repositories from a CSV file."""
    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            # Construct source and target URLs with credentials
            credentials = f"{on_prem['username']}:{urllib.parse.quote_plus(on_prem['password'])}"
            source_url = row['source']

            # Check if the URL starts with http:// or https://
            if source_url.startswith('http://'):
                new_url = source_url.replace('http://', f"http://{credentials}@")
            elif source_url.startswith('https://'):
                new_url = source_url.replace('https://', f"https://{credentials}@")
            
            source_url = new_url
            target_url = row['target']
            repo_folder = os.path.join(save_folder, row['name'])

            logging.info(f"Processing [{row['name']}] repository...")

            if should_clone:
                # Clone repository if it does not exist
                if not os.path.exists(repo_folder):
                    clone_command = f"git clone {source_url} \"{repo_folder}\""
                    run_command(clone_command)
                else:
                    logging.info("Repository already exists, skipping clone.")

                # Add cloud remote
                remote_add_command = f"git remote add cloud {target_url}"
                run_command(remote_add_command, cwd=repo_folder)

            if should_sync_lfs:
                # Fetch and push LFS files
                logging.info("Fetching LFS files...")
                run_command("git lfs fetch --all", cwd=repo_folder)
                logging.info("Pushing LFS files...")
                run_command("git lfs push --all cloud", cwd=repo_folder)

# Main execution
if __name__ == "__main__":
    clone_and_sync_repos()
