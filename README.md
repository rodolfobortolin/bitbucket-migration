# Bitbucket Migration Series: From Data Center to Cloud

## Overview
This repository contains scripts and resources to assist in the migration from Bitbucket Data Center to Bitbucket Cloud. The series addresses gaps in the Bitbucket Cloud Migration Assistant (BCMA), providing solutions for components not automatically migrated by BCMA.

## Blog Post Series
The series is divided into six posts, each focusing on a specific aspect of the migration process:

1. **[Migrating Git Large File Storage (LFS) to Bitbucket Cloud]([link-to-post-1](https://atlassianexpert.tips/2024/05/09/1-6-migrating-git-large-file-storage-lfs-to-bitbucket-cloud/))**
2. **[Updating Repository References to Bitbucket Cloud]([link-to-post-2](https://atlassianexpert.tips/2024/05/15/2-6-updating-repository-references-to-bitbucket-cloud/))**
3. **[Migrating Reviewer to Bitbucket Cloud]([link-to-post-3](https://atlassianexpert.tips/2024/05/29/3-6-migrating-reviewers-to-bitbucket-cloud/))**
4. **Migrating Groups and Memberships to Bitbucket Cloud (Coming Soon)**
5. **Migrating Repository Permissions to Bitbucket Cloud (Coming Soon)**
6. **Migrating Personal Repositories to Bitbucket Cloud (Coming Soon)**

## Understanding BCMA Limitations
BCMA automates many migration tasks but has several limitations, including but not limited to:

- Repository Git information
- Forked repository associations
- Git submodules
- Pull request attachments
- Duplicate repository names
- Open changes on local machines
- Extra-large repositories (over 10GB)
- Personal repositories
- Repository settings
- Branch permissions
- Webhooks management
- Merge checks
- Build statuses
- Project data
- User and group permissions
- Avatars, passwords, timezones, SSH keys, and app passwords

## How This Series Helps
The provided scripts and guides in this series cover areas not handled by BCMA, ensuring a more comprehensive migration process.

### Covered Topics:
- **Git Large File Storage (LFS):** Migrating large files to maintain repository integrity.
- **Repository References:** Updating references to point to the new cloud environment.
- **Reviewer Settings:** Preserving code review and approval workflows.
- **Groups and Memberships:** Transferring group data and memberships.
- **Repository Permissions:** Replicating permissions to safeguard security policies.
- **Personal Repositories:** Ensuring individual projects are migrated correctly.

## Repository Contents
The repository is structured as follows:

- `1-list-repos.py`: Lists all repositories in the Bitbucket Data Center.
- `2-clone-repos-with-lfs.py`: Clones repositories with Git LFS enabled.
- `3-ref-update.py`: Updates repository references to point to Bitbucket Cloud.
- `4-sync-project-branches.py`: Synchronizes project branches between Data Center and Cloud.
- `5-user-export.py`: Exports user data from Bitbucket Data Center.
- `6-sync-reviewers.py`: Syncs reviewer settings to Bitbucket Cloud.
- `7-transfer-groups.py`: Transfers group data to Bitbucket Cloud.
- `8-add-group-membership.py`: Adds group memberships in Bitbucket Cloud.
- `9-transfer-repo-permissions.py`: Transfers repository permissions to Bitbucket Cloud.
- `10-transfer-personal-repos.py`: Transfers personal repositories to Bitbucket Cloud.
- `config.py`: Configuration file for setting up script parameters.
- `group-membership.csv`: CSV file containing group membership details.
- `personal-repos.csv`: CSV file containing personal repository details.
