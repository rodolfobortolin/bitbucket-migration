import csv
import os
import re
import subprocess
import logging
from config import cloud, on_prem, repository_folder

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration Variables - Customize these as needed
script_location = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.join(script_location, "merged_repositories.csv")  # Adjusted for script location
folder = os.getcwd()  # Folder containing the repositories

should_push = True  # Whether to push changes to the remote repository

def run_command(command, cwd=None):
    """Execute a system command with optional working directory."""
    try:
        subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"Successfully executed: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {' '.join(command)}\n{e.stdout.decode()}")

def replace_references_in_file(filepath, patterns):
    """Replace patterns in a file based on provided mappings."""
    if not os.path.exists(filepath):
        logging.warning(f"File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = file.read()
        if data: 
            for pattern, subst in patterns.items():
                data = re.sub(pattern, subst, data, 0, re.MULTILINE)

            with open(filepath, "w") as file:
                file.write(data)
            logging.info(f"Updated references in file: {filepath}")
    except Exception as e:
        logging.exception(f"Error processing file: {filepath}")

def commit_and_push_changes(repo_folder, branch="master"):
    """Commit changes in the repository and push them to the cloud."""
    try:
        # Check for uncommitted changes
        status_output = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo_folder).decode().strip()
        if status_output:
            # Stage all changes
            subprocess.run(["git", "add", "."], cwd=repo_folder, check=True)
            # Commit changes
            subprocess.run(["git", "commit", "-m", "Update domain references"], cwd=repo_folder, check=True)
            # Push changes
            subprocess.run(["git", "push", "cloud", branch], cwd=repo_folder, check=True)
            logging.info(f"Changes pushed for {os.path.basename(repo_folder)}.")
        else:
            logging.info(f"No changes to commit for {os.path.basename(repo_folder)}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {os.path.basename(repo_folder)}: {e}")

def process_repository(repo_folder, patterns):
    """Process files in a repository folder to replace references and commit changes."""
    for root, _, files in os.walk(repo_folder):
        for name in files:
            filepath = os.path.join(root, name)
            replace_references_in_file(filepath, patterns)

    if should_push:
        commit_and_push_changes(repo_folder)

def main():
    patterns = {
        rf"(ssh://git@{on_prem['domain']}/)(?:.*)/(?P<repository>.*\.git)": f"git@bitbucket.org:{cloud['workspace']}/\\g<repository>",
        rf"(http?://{on_prem['domain']})(?:.*)/(?P<repository>.*\.git)": f"https://bitbucket.org/{cloud['workspace']}/\\g<repository>"
    }

    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            repo_folder = os.path.join(folder, repository_folder, row['name'])
            logging.info(f"Processing repository: {row['name']}")
            process_repository(repo_folder, patterns)

if __name__ == "__main__":
    main()
