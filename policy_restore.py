#!/usr/bin/python
"""
OneFuse Policy Restore Script

This script will: 
1. Use git to pull content from git repo to FILE_PATH set below
2. Connect to OneFuse via REST and restore all OneFuse Policies in the FILE_PATH

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

Use: 
1. Copy the entire onefuse_backups directory to /var/opt/cloudbolt/proserv/xui/ on the OneFuse appliance
2. This script can be executed by:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py

NOTE: If you have used this script to restore any credentials, this script does not store or restore
passwords. If credentials are restored to an instance, you will need to update the password for each 
restored credential. If the credentials already existed, this script will not overwrite the existing 
password, but will update all other properties of a credential.
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
import subprocess
from os import listdir
from os.path import isfile, join

FILE_PATH = '/var/opt/cloudbolt/proserv/se-onefuse-dev2_backups/'

def create_restore_content(json_content,onefuse,policy_type):
    restore_json = {}
    for key in json_content:
        if key == "_links":
            for key2 in json_content["_links"]:
                if key2 != "self":
                    if isinstance(json_content["_links"][key2],dict):
                        href = json_content["_links"][key2]["href"]
                        link_name = json_content["_links"][key2]["title"]
                        link_type = href.replace('/api/v3/onefuse','').split('/')[1]
                        link_id = get_link_id(onefuse,link_type,link_name,policy_type,json_content)
                        restore_json[key2] = link_id
                    elif isinstance(json_content["_links"][key2],list):
                        restore_json[key2] = []
                        for link in json_content["_links"][key2]:
                            href = link["href"]
                            link_name = link["title"]
                            link_type = href.replace('/api/v3/onefuse','').split('/')[1]
                            link_id = get_link_id(onefuse,link_type,link_name,policy_type,json_content)
                            restore_json[key2].append(link_id)
                    else: 
                        print(f'Unknown type found: {type(json_content["_links"][key2])}')
        elif key != 'id':
            restore_json[key] = json_content[key]
    return restore_json

def get_link_id(onefuse,link_type,link_name,policy_type,json_content):
    if link_type == 'endpoints':
        endpoint_type = json_content["type"]
        url = f'/{link_type}/?filter=name.iexact:"{link_name}";type.iexact:"{json_content["type"]}"'
    else: 
        url = f'/{link_type}/?filter=name.iexact:"{link_name}"'
    print(f"linkurl: {url}")
    link_response = onefuse.get(url)
    link_response.raise_for_status()
    link_json = link_response.json()
    if link_json["count"] == 1:
        return link_json["_embedded"][link_type][0]["_links"]["self"]["href"]
    else: 
        error_string = (f'Link not found. link_type: {link_type}'
                        f'link_name: {link_name}')
        raise Exception(error_string)

def main():
    policy_types = [
        "moduleCredentials","endpoints","validators"#,"namingSequences","namingPolicies","propertySets","ipamPolicies","dnsPolicies","microsoftADPolicies","ansibleTowerPolicies",
        #"scriptingPolicies","servicenowCMDBPolicies","vraPolicies"
    ]

    #Use git to synch changes to repo
    GIT_PATH = f'{FILE_PATH}.git'
    git_args = [
        ['git', f'--work-tree={FILE_PATH}', f'--git-dir={GIT_PATH}','pull'],
    ]
    for args in git_args:
        res = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, _error = res.communicate()
        if not _error:
            print(output)
        else:
            print(_error)

    #Gather policies from FILE_PATH, restore them to OneFuse
    with OneFuseConnector("onefuse") as onefuse:
        for policy_type in policy_types:
            print(f'Restoring policy_type: {policy_type}')
            policy_type_path = f'{FILE_PATH}{policy_type}/'
            if os.path.exists(os.path.dirname(policy_type_path)):
                policy_files = [f for f in listdir(policy_type_path) if isfile(join(policy_type_path, f))]
                for file_name in policy_files:
                    f = open(f'{policy_type_path}{file_name}','r')
                    content = f.read()
                    json_content = json.loads(content)
                    policy_name = json_content["name"]
                    
                    if "type" in json_content:
                        url = f'/{policy_type}/?filter=name.iexact:"{policy_name}";type.iexact:"{json_content["type"]}"'
                    elif "endpointType" in json_content:
                        url = f'/{policy_type}/?filter=name.iexact:"{policy_name}";endpointType.iexact:"{json_content["endpointType"]}"'
                    else: 
                        url = f'/{policy_type}/?filter=name.iexact:"{policy_name}"'
                    #Check does policy exist
                    response = onefuse.get(url)
                    print(f'url: {url}')
                    #Check for errors. If "Not Found." returned continue to next file_name
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
                            print(f"WARN: policy_type not found: {policy_type}, file_name: {file_name}")
                            continue
                        else: 
                            error_string = (f'Unknown error. JSON: {response.json()}, ')
                            error_string += (f'Error: {sys.exc_info()[0]}. {sys.exc_info()[1]}, '
                                            f'line: {sys.exc_info()[2].tb_lineno}')
                            raise Exception(error_string)

                    response_json = response.json()
                    if response_json["count"] == 0:
                        print(f'Creating OneFuse Content. policy_type: {policy_type}, file_name: {file_name}')
                        url = f'/{policy_type}/'
                        restore_content = create_restore_content(json_content,onefuse,policy_type)
                        if policy_type == "moduleCredentials": 
                            restore_content["password"] = "Pl@ceHolder123!"
                            print("WARN: Your credential has been restored but before it can be used"
                                  f" you must update the password for the credential: {file_name}")
                        response = onefuse.post(url,json=restore_content)
                        try: 
                            response.raise_for_status()
                        except: 
                            print(f'url: {url}, restore_content: {restore_content}')
                    elif response_json["count"] == 1:
                        print(f'Updating OneFuse Content. policy_type: {policy_type}, file_name: {file_name}')
                        policy_json = response_json["_embedded"][policy_type][0]
                        policy_id = policy_json["id"]
                        url = f'/{policy_type}/{policy_id}/'
                        restore_content = create_restore_content(json_content,onefuse,policy_type)
                        response = onefuse.put(url,json=restore_content)
                        response.raise_for_status()
                    else:    
                        err_str = (f'WARN: More than one policy was found with the'
                                  f' name: {policy_name} and type: {policy_type}. '
                                  f'Skipping policy restore')
                        print(err_str)
            else:
                print(f'Directory for policy type: {policy_type} does not exist. Skipping.')            


if __name__ == "__main__":
    main()