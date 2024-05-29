
# Bitbucket Cloud configurations
cloud = {
    'workspace': '',  # The workspace ID for Bitbucket Cloud
    'username': '',  # Your Bitbucket Cloud username: https://bitbucket.org/account/settings/
    'token': '',  # Your Bitbucket Cloud app password: https://bitbucket.org/account/settings/app-passwords/new
    'bitbucket_cloud_repositories' : 'bitbucket_cloud_repositories.csv'  # Output CSV file for Cloud repositories
}

# Bitbucket Server configurations
on_prem = {
    'base_url': 'http://localhost:7990',  # The base URL of your Bitbucket Server instance
    'username': 'rbortolin',  # Your Bitbucket Server username
    'password': 'admin',  # Your Bitbucket Server password
    'domain': 'localhost:7990',
    'bitbucket_server_repositories' : 'bitbucket_server_repositories.csv'  # Output CSV file for Server repositories
}

repository_folder = 'repositories' #the directory which the script will download the repositories (for 2-close-repos-with-lfs.py)
project_key = "PERSONAL"

"""

Query the database to get the group-membership.csv

SELECT u.user_name,
	   u.display_name,
       g.group_name
 FROM cwd_membership m
 INNER JOIN cwd_user u ON m.child_id = u.id
 INNER JOIN cwd_group g ON m.parent_id = g.id
 INNER JOIN cwd_directory d ON g.directory_id = d.id 
 ORDER BY d.directory_name, u.user_name, g.group_name;

result: 

"user_name","display_name","group_name"
"rbortolin","Rodolfo Bortolin","group-1"

--------------------

Query to get all the personal repos to personal-repos.csv


SELECT
       prj.name AS "User",
       rep.slug AS "Repository Slug",
       rep.description AS "Repository Descr"
FROM repository rep
INNER JOIN project prj ON rep.project_id = prj.id and prj.project_type = 1
LEFT JOIN STA_NORMAL_PROJECT np ON prj.id = np.project_id
ORDER BY "User";

result: 

"User","Repository Slug","Repository Descr"
"~rbortolin","personal",NULL


"""
