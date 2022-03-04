#!/usr/bin/python
"""
OneFuse Policy Backup Script

This is a sample script to get you started syncing OneFuse backups with git.
This is intended as a sample only, it may need to be updated to match your
specific use case.

This script will:
1. Connect to OneFuse via REST and store all OneFuse Policies in JSON in a local directory
2. Use git to synch policies to a git repo

Pre-Requisites: 
1. Logged in to the OneFuse appliance as root, install the OneFuse Python Module:
    https://docs.cloudbolt.io/articles/#!onefuse-latest/python-module-getting-started
2. Create a Connection Info for onefuse. This must be labelled as 'onefuse', and named 'onefuse'
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
    > mkdir /var/opt/cloudbolt/proserv/<directory name here>
    > cd /var/opt/cloudbolt/proserv/<directory name here>
    > git clone https://<git username>:<git password>@github.com/<repo url>
4. Update BACKUPS_PATH below to reflect the subdirectory under the folder where
   you would like backups to end up. This would allow for multiple OneFuse 
   instances to backup to the same git repo. To only backup a single OneFuse
   instance, GIT_PATH can equal BACKUPS_PATH
5. Update GIT_PATH below to reflect the directory where the repo was cloned to
6. Update GIT_AUTHOR below to reflect the author information

Use: 
1. Copy the policy_backups.py script to /var/opt/cloudbolt/proserv/onefuse_backups/ on the OneFuse appliance
2. This script can be executed by:
    > python /var/opt/cloudbolt/proserv/onefuse_backups/policy_backups.py

This script can also be scheduled using cron if desired to have schedule policy backups/versioning
"""


if __name__ == '__main__':
    import os
    import sys
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.append('/opt/cloudbolt')
    django.setup()


from onefuse.cloudbolt_admin import CbOneFuseManager
from onefuse.backups import BackupManager
import subprocess


BACKUPS_PATH = '/var/opt/cloudbolt/proserv/se-1f-demo-backups/cb-mb-01/'
GIT_PATH = '/var/opt/cloudbolt/proserv/se-1f-demo-backups/'
GIT_AUTHOR = 'OneFuse Admin <onefuse@cloudbolt.io>' #format: 'First Last <email@domain.com>', there must be a space between Last and <
CONN_INFO_NAME = "onefuse"


def main():
    ofm = CbOneFuseManager(CONN_INFO_NAME)
    backups = BackupManager(ofm)
    backups.backup_policies(BACKUPS_PATH)
          
    #Use git to synch changes to repo
    GIT_FILE = f'{GIT_PATH}.git'
    git_args = [
        ['git', f'--work-tree={GIT_PATH}', f'--git-dir={GIT_FILE}','pull'],
        ['git', f'--work-tree={GIT_PATH}', f'--git-dir={GIT_FILE}', 'add', '.'],
        ['git', f'--work-tree={GIT_PATH}', f'--git-dir={GIT_FILE}', 'commit', '-a', '-m "OneFuse Backup"', f'--author={GIT_AUTHOR}'],
        ['git', f'--work-tree={GIT_PATH}', f'--git-dir={GIT_FILE}', 'push']
    ]
    for args in git_args:
        res = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, _error = res.communicate()

        if not _error:
            print(output)
        else:
            print(_error)

if __name__ == "__main__":
    main()