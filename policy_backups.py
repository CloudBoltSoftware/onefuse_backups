#!/usr/bin/python
"""
OneFuse Policy Backup Script

This script will: 
1. Connect to OneFuse via REST and store all OneFuse Policies in JSON in a local directory
2. Use git to synch policies to a git repo

Pre-Requisites: 
1. Create a Connection Info for onefuse. This must be labelled as 'onefuse', and named 'onefuse'
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
2. Use Git to clone repo to somewhere under /var/opt/cloudbolt/proserv/
    > mkdir /var/opt/cloudbolt/proserv/<directory name here>
    > cd /var/opt/cloudbolt/proserv/<directory name here>
    > git clone https://<git username>:<git password>@github.com/<repo url>
3. Update FILE_PATH below to reflect the directory where the repo was cloned to
4. Update GIT_AUTHOR below to reflect the author information

Use: 
1. Copy the entire onefuse_backups directory to /var/opt/cloudbolt/proserv/xui/ on the OneFuse appliance
2. This script can be executed by:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_backups.py

This script can also be scheduled using cron if desired to have schedule policy backups/versioning
"""


if __name__ == '__main__':
    import os
    import sys
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.append('/opt/cloudbolt')
    django.setup()

import sys
import json
from api_wrapper import OneFuseConnector
import os
import errno
import subprocess



FILE_PATH = '/var/opt/cloudbolt/proserv/onefuse_backups/se-onefuse-dev2_backups/'
GIT_AUTHOR = 'OneFuse Admin <onefuse@cloudbolt.io>' #format: 'First Last <email@domain.com>', there must be a space between Last and <

def create_json_files(response,policy_type,onefuse):
    try:
        response.raise_for_status()
    except:
        try: 
            detail = response.json()["detail"]
        except: 
            error_string = (f'Unknown error. JSON: {response.json()}, ')
            error_string += (f'Error: {sys.exc_info()[0]}. {sys.exc_info()[1]}, '
                            f'line: {sys.exc_info()[2].tb_lineno}')
            raise Exception(error_string)
        if detail == 'Not found.':
            #This may happen when script is run against older versions. 
            print(f"WARN: policy_type not found: {policy_type}")
            return False
        else: 
            error_string = (f'Unknown error. JSON: {response.json()}, ')
            error_string += (f'Error: {sys.exc_info()[0]}. {sys.exc_info()[1]}, '
                            f'line: {sys.exc_info()[2].tb_lineno}')
            raise Exception(error_string)
    
    response_json = response.json()
    
    for policy in response_json["_embedded"][policy_type]:
        #print(f'policy: {policy}')
        #print(f'Backing up {policy_type} policy: {policy["name"]}')
        filename = f'{FILE_PATH}{policy_type}/{policy["name"]}'
        if policy_type == "endpoints":
            if "credential" in policy["_links"]:
                policy["_links"]["credential"]["title"] = get_credential_name(policy,onefuse)                
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        if "type" in policy:
            file_name = f'{FILE_PATH}{policy_type}/{policy["type"]}_{policy["name"]}.json'
        elif "endpointType" in policy:
            file_name = f'{FILE_PATH}{policy_type}/{policy["endpointType"]}_{policy["name"]}.json'
        else: 
            file_name = f'{FILE_PATH}{policy_type}/{policy["name"]}.json'
        f = open(file_name,'w+')
        f.write(json.dumps(policy, indent=4))
        f.close()
    
    return key_exists(response_json["_links"], "next")

def get_credential_name(policy,onefuse): 
    href = policy["_links"]["credential"]["href"]
    url = href.replace('/api/v3/onefuse','')
    response = onefuse.get(url)
    try:
        response.raise_for_status()
    except: 
        err_msg = f'Link could not be found for href: {href}'
        raise Exception(err_msg)
    return response.json()["name"]

def key_exists(dict, key):  
    if key in dict.keys():
        return True
    else:
        return False 

def main():
    policy_types = [
        "moduleCredentials","endpoints","validators","namingSequences","namingPolicies","propertySets","ipamPolicies","dnsPolicies","microsoftADPolicies","ansibleTowerPolicies",
        "scriptingPolicies","servicenowCMDBPolicies","vraPolicies"
    ]

    #Gather policies from OneFuse, store them under FILE_PATH
    with OneFuseConnector("onefuse") as onefuse:
        for policy_type in policy_types:
            print(f'Backing up policy_type: {policy_type}')
            response = onefuse.get(f'/{policy_type}/')
            next_exists = create_json_files(response,policy_type,onefuse)
            while next_exists:
                next_page = response.json()["_links"]["next"]["href"]
                next_page = next_page.split("/?")[1]
                response = onefuse.get(f'/{policy_type}/?{next_page}')
                next_exists = create_json_files(response,policy_type,onefuse)

          
    #Use git to synch changes to repo
    GIT_PATH = f'{FILE_PATH}.git'
    git_args = [
        ['git', f'--work-tree={FILE_PATH}', f'--git-dir={GIT_PATH}','pull'],
        ['git', f'--work-tree={FILE_PATH}', f'--git-dir={GIT_PATH}', 'add', '.'],
        ['git', f'--work-tree={FILE_PATH}', f'--git-dir={GIT_PATH}', 'commit', '-a', '-m "OneFuse Backup"', f'--author={GIT_AUTHOR}'],
        ['git', f'--work-tree={FILE_PATH}', f'--git-dir={GIT_PATH}', 'push']
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