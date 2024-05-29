    
import csv
import requests
from requests.auth import HTTPBasicAuth
import logging
import json
import os
from config import cloud, on_prem  # Import authorization configurations

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def extract_repo_slug(target_url):
    # Convert the target URL into a repository slug
    if target_url.endswith('.git'):
        target_url = target_url[:-4]
    parts = target_url.split('/')
    if parts and 'bitbucket.org' in target_url:
        return parts[-1]
    return None

def update_branch_model(repo_slug, branch_model_settings):
    """ Update the branch model settings for a repository. """
    url = f"https://api.bitbucket.org/2.0/repositories/{cloud['workspace']}/{repo_slug}/branching-model/settings"
    response = requests.put(
        url,
        json=branch_model_settings,
        auth=HTTPBasicAuth(cloud['username'], cloud['token']),
        headers={"Accept": "application/json"}
    )
    if response.status_code == 200:
        logging.info(f"Branch model updated successfully for {repo_slug}")
    else:
        logging.error(f"Failed to update branch model for {repo_slug}: {response.status_code} {response.text}")

def update_branch_restrictions(repo_slug, branch_restrictions_payload):
    """ Update the branch restrictions for a repository. """
    url = f"https://api.bitbucket.org/2.0/repositories/{cloud['workspace']}/{repo_slug}/branch-restrictions"
    response = requests.post(
        url,
        json=branch_restrictions_payload,
        auth=HTTPBasicAuth(cloud['username'], cloud['token']),
        headers={"Accept": "application/json"}
    )
    if response.status_code in [200, 201]:
        logging.info(f"Branch restrictions updated successfully for {repo_slug}")
    else:
        logging.error(f"Failed to update branch restrictions for {repo_slug}: {response.status_code} {response.text}")

def main():
    # Load branch model settings from a file or define them here
    branch_model_settings = {
        "development": {
            "use_mainbranch": True
        },
        "production": {
            "enabled": False,
            #"use_mainbranch": False,
            #"branch": {"name": "production"}
        },
        "branch_types": [
            {
                "kind": "bugfix",
                "prefix": "bugfix/",
                "enabled": True
            },
            {
                "kind": "feature",
                "prefix": "feature/",
                "enabled": True
            },
            {
                "kind": "hotfix",
                "prefix": "hotfix/",
                "enabled": True
            },
            {
                "kind": "release",
                "prefix": "release/",
                "enabled": True
            }
        ]
    }
    
    # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-branch-restrictions/#api-repositories-workspace-repo-slug-branch-restrictions-post
    # Must be one of: 
        # push
        # delete
        # force
        # restrict_merges
        # require_tasks_to_be_completed
        # require_approvals_to_merge
        # require_review_group_approvals_to_merge
        # require_default_reviewer_approvals_to_merge
        # require_no_changes_requested
        # require_passing_builds_to_merge
        # require_commits_behind
        # reset_pullrequest_approvals_on_change
        # smart_reset_pullrequest_approvals, 
        # reset_pullrequest_changes_requested_on_change
        # require_all_dependencies_merged 
        # enforce_merge_checks
        # allow_auto_merge_when_builds_pass
        
    
    branch_restriction_1 = {
        "kind": "require_tasks_to_be_completed",
        "pattern": "develop"
    }
    
    branch_restriction_2 = {
        "kind": "force",
        "pattern": "*"
    }
    

    merged_repositories_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'merged_repositories.csv')

    with open(merged_repositories_path, mode='r', newline='') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['match'].lower() == 'yes':
                repo_slug = extract_repo_slug(row['target'])
                if repo_slug:
                    update_branch_model(repo_slug, branch_model_settings)
                    update_branch_restrictions(repo_slug, branch_restriction_1)
                    update_branch_restrictions(repo_slug, branch_restriction_2)
if __name__ == "__main__":
    main()
