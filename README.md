# OneFuse Backup and Restore Scripts
This repo contains a sample script to back up OneFuse Policies to a git repo. These are only intended as samples only, and should not be used in production environments. 

To learn more about OneFuse Backups and Policy Restores, the documentation can be found at:

[Backup OneFuse Policies](https://docs.cloudbolt.io/articles/#!onefuse-latest/backup-onefuse-policies-with-onefuse-python-module)

[Restore OneFuse Policies](https://docs.cloudbolt.io/articles/#!onefuse-latest/restore-onefuse-policies-with-onefuse-python-module)


## Setup/Pre-Requisites
1. Copy the policy_backups.py script to /var/opt/cloudbolt/proserv/onefuse_backups/
   on the OneFuse appliance. If the onefuse_backups directory doesn't exist, you can create it. 
2. Create a Connection Info for onefuse. This must be labelled as 'onefuse', 
   and named 'onefuse'. 
    - To do this manually from shell plus ssh in to the OneFuse appliance and then: 
        ```
        python /opt/cloudbolt/manage.py shell_plus
        ci = ConnectionInfo(
            name='onefuse',
            username='<username>',
            password='<password>',
            ip='<onefuse fqdn>',
            port=<port>,
            protocol='https'
        )
        ci.save()
        ci.labels.add('onefuse')
        ci.save()
        ```
3. Use Git to clone repo to somewhere under /var/opt/cloudbolt/proserv/
    ```
    cd /var/opt/cloudbolt/proserv/<directory name here if desired>
    git clone https://<git username>:<git password>@github.com/<repo url>
    ```


## OneFuse Policy Backups Script
### Purpose
The backup script will: 
1. Connect to OneFuse via REST and store all OneFuse Policies in JSON in a local directory
2. Use git to synch policies to a git repo

### Policy Backup Setup:
1. Update BACKUPS_PATH in the policy_backups.py script to reflect the subdirectory under the folder where you would like backups to end up. This would allow for multiple OneFuse instances to backup to the same git repo. To only backup a single OneFuse instance, GIT_PATH can equal BACKUPS_PATH
2. Update GIT_PATH in the policy_backups.py script to reflect the directory where the repo was cloned to
3. Update GIT_AUTHOR in the policy_backups.py script to reflect the author information

### Execution
Execute backups by:
  
    python /var/opt/cloudbolt/proserv/onefuse_backups/policy_backups.py

    
## OneFuse Policy Restore Script
Restores can now be completed by using the OneFuse Python Module. 
https://docs.cloudbolt.io/articles/#!onefuse-latest/restore-onefuse-policies-with-onefuse-python-module