# OneFuse Backup and Restore Scripts
This repo contains sample scripts to back up OneFuse Policies to a git repo and potentially restore them to an instance. These are only intended as samples only, and should not be used in production environments. 

## Setup/Pre-Requisites
1. Copy the entire onefuse_backups repo to /var/opt/cloudbolt/proserv/xui/
   on the OneFuse appliance. If the xui directory doesn't exist, you can create it. 
2. Create a Connection Info for onefuse. This must be labelled as 'onefuse', 
   and named 'onefuse'
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
1. Update BACKUPS_PATH below to reflect the subdirectory under the folder where you would like backups to end up. This would allow for multiple OneFuse instances to backup to the same git repo. To only backup a single OneFuse instance, GIT_PATH can equal BACKUPS_PATH
2. Update GIT_PATH below to reflect the directory where the repo was cloned to
3. Update GIT_AUTHOR below to reflect the author information

### Execution
Execute bacvkups by:
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_backups.py
    ```
    
    
    
## OneFuse Policy Restore Script
### Purpose
The restore script will: 
1. Use git to pull content from git repo to FILE_PATH set below
2. Connect to OneFuse via REST and restore all OneFuse Policies in the FILE_PATH

### Policy Restore Setup:
1. Update the FILE_PATH variable in the policy_restore.py to reflect the directory in the cloned repo that you would like to restore from.

### Execution
Execute a restore by:
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py
    ```
###Restore Note: 
If you use the restore script to restore any credentials, the script does
not store or restore passwords. If credentials are created for an instance, you
will need to update the password for each created credential. If the credentials
already existed, this script will not overwrite the existing password, but will
update all other properties of a credential.



## OneFuse Restore Specific Policies Script
### Purpose
1. Restore all files to OneFuse passed in as args to the script.
2. This script can restore OneFuse JSON policies either from a file on the 
   local system or directly from a git repo. 
3. This script is not aware of policy dependencies. If you have dependencies
   (eg. Naming Policy needs a Naming Sequence, or Endpoint needs Credentials)
   You will also need to pass in the json for the dependency as an argument 
   prior to the dependent policy.

### Execution
1. This script can be executed by:
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py <arg1> <arg2> <arg3>
    ```
   
### Examples
1. Restore a single Naming Policy from file
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingPolicies/docker_port.json'
    ```
2. Restore Naming Policy where dependency of Naming Sequence doesn't already exist on the server. Note: the dependency is called first:
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingSequences/BASE10_port.json' '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingPolicies/docker_port.json'
    ```
3. Restore a namingPolicy from a git repo. Note: be sure to use the raw link here. If it is a private repo, you will also want to include your token in the url.     
    ```
    python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py https://raw.githubusercontent.com/CloudBoltSoftware/se-1f-demo-backups/main/se-1f-demo-1-3/namingPolicies/test_backups.json
    ```
 
