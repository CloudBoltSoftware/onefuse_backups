# OneFuse Backup and Restore Scripts
This repo contains scripts required to back up OneFuse Policies to a git repo and potentially restore them to an instance. 

## Setup/Pre-Requisites
1. Copy the entire onefuse_backups repo to /var/opt/cloudbolt/proserv/xui/
   on the OneFuse appliance
2. Create a Connection Info for onefuse. This must be labelled as 'onefuse', 
   and named 'onefuse'
    - To do this manually from shell plus: 
        > python /opt/cloudbolt/manage.py shell_plus
        > ci = ConnectionInfo(
              name='onefuse',
              username='<username>',
              password='<password>',
              ip='<onefuse fqdn>',
              port=<port>,
              protocol='https'
          )
        > ci.save()
        > ci.labels.add('onefuse')
        > ci.save()
3. Use Git to clone repo to somewhere under /var/opt/cloudbolt/proserv/
    > cd /var/opt/cloudbolt/proserv/<directory name here if desired>
    > git clone https://<git username>:<git password>@github.com/<repo url>

## OneFuse Policy Backups Script
### Purpose
The backup script will: 
1. Connect to OneFuse via REST and store all OneFuse Policies in JSON in a local directory
2. Use git to synch policies to a git repo

### Policy Backup Setup:
1. Update the FILE_PATH variable in policy_backups.py to reflect the directory where the repo is cloned to.
2. Update the GIT_AUTHOR variable in policy_backups.py to reflect who any commits should be attributed to. 

### Execution
Execute bacvkups by:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_backups.py

## OneFuse Policy Restore Script
### Purpose
The restore script will: 
1. Use git to pull content from git repo to FILE_PATH set below
2. Connect to OneFuse via REST and restore all OneFuse Policies in the FILE_PATH

### Policy Restore Setup:
1. Update the FILE_PATH variable in the policy_restore.py to reflect the directory where the repo is cloned to.

### Execution
Execute a restore by:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py

###Restore Note: 
If you use the restore script to restore any credentials, the script does
not store or restore passwords. If credentials are created for an instance, you
will need to update the password for each created credential. If the credentials
already existed, this script will not overwrite the existing password, but will
update all other properties of a credential.
