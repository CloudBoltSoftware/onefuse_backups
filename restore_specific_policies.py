#!/usr/bin/python
"""
OneFuse Restore Specific Policies

This script will: 
1. Restore all files to OneFuse passed in as args to the script.
2. This script can restore OneFuse JSON policies either from a file on the 
   local system or directly from a git repo. 
3. This script is not aware of policy dependencies. If you have dependencies
   (eg. Naming Policy needs a Naming Sequence, or Endpoint needs Credentials)
   You will also need to pass in the json for the dependency as an argument 
   prior to the dependent policy.

Pre-Requisites: 
1. Create a Connection Info for onefuse. This must be labelled as 'onefuse', 
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

Use: 
1. This script can be executed by:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py <arg1> <arg2> <arg3>
   
Examples: 
1. Restore a single Naming Policy from file
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingPolicies/docker_port.json'
2. Restore Naming Policy where dependency of Naming Sequence doesn't already 
   exist on the server. Note: the dependency is called first:
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingSequences/BASE10_port.json' '/var/opt/cloudbolt/proserv/se-1f-demo-backups/se-1f-demo-1-3/namingPolicies/docker_port.json'
3. Restore a namingPolicy from a git repo. Note: be sure to use the raw link
   here. If it is a private repo, you will also want to include your token in
   the url.     
    > python /var/opt/cloudbolt/proserv/xui/onefuse_backups/policy_restore.py https://raw.githubusercontent.com/CloudBoltSoftware/se-1f-demo-backups/main/se-1f-demo-1-3/namingPolicies/test_backups.json
     
NOTE: If you have used this script to restore any credentials, this script does
not store or restore passwords. If credentials are restored to an instance, you
will need to update the password for each restored credential. If the credentials
already existed, this script will not overwrite the existing password, but will
update all other properties of a credential.
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
import requests

def create_restore_content(json_content,onefuse,policy_type):
    restore_json = {}
    for key in json_content:
        if key == "_links":
            for key2 in json_content["_links"]:
                if key2 != "self":
                    if isinstance(json_content["_links"][key2],dict):
                        href = json_content["_links"][key2]["href"]
                        link_name = json_content["_links"][key2]["title"]
                        link_type = href.replace('/api/v3/onefuse','')
                        link_type = link_type.split('/')[1]
                        link_id = get_link_id(onefuse,link_type,link_name,
                                              policy_type,json_content)
                        restore_json[key2] = link_id
                    elif isinstance(json_content["_links"][key2],list):
                        restore_json[key2] = []
                        for link in json_content["_links"][key2]:
                            href = link["href"]
                            link_name = link["title"]
                            link_type = href.replace('/api/v3/onefuse','')
                            link_type = link_type.split('/')[1]
                            link_id = get_link_id(onefuse,link_type,link_name,
                                                  policy_type,json_content)
                            restore_json[key2].append(link_id)
                    else: 
                        print(f'Unknown type found: '
                              f'{type(json_content["_links"][key2])}')
        elif key != 'id' and key != 'microsoftEndpoint':
            restore_json[key] = json_content[key]
    return restore_json

def get_link_id(onefuse,link_type,link_name,policy_type,
                json_content):
    if link_type == 'endpoints':
        if policy_type == "microsoftADPolicies":
            endpoint_type = "microsoft"
        elif policy_type == "ansibleTowerPolicies":
            endpoint_type = "ansible_tower"
        elif policy_type == "servicenowCMDBPolicies":
            endpoint_type = "servicenow"
        else:
            endpoint_type = json_content["type"]
        url = (f'/{link_type}/?filter=name.iexact:"{link_name}";'
               f'type.iexact:"{endpoint_type}"')
    else: 
        url = f'/{link_type}/?filter=name.iexact:"{link_name}"'
    #print(f"linkurl: {url}")
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
    args = sys.argv
    args.pop(0)

    #Gather policies from FILE_PATH, restore them to OneFuse
    with OneFuseConnector("onefuse") as onefuse:
        for file_path in args:
            if file_path.find('http') == -1:
                f = open(f'{file_path}','r')
                content = f.read()
            else: 
                response = requests.get(file_path)
                response.raise_for_status()
                content = response.content
            json_content = json.loads(content)
            policy_name = json_content["name"]
            policy_type = json_content["_links"]["self"]["href"].split('/')[4]
            
            if "type" in json_content:
                url = (f'/{policy_type}/?filter=name.iexact:"{policy_name}";'
                        f'type.iexact:"{json_content["type"]}"')
            elif "endpointType" in json_content:
                url = (f'/{policy_type}/?filter=name.iexact:"{policy_name}";'
                        f'endpointType.iexact:"{json_content["endpointType"]}"')
            else: 
                url = f'/{policy_type}/?filter=name.iexact:"{policy_name}"'
            #Check does policy exist
            response = onefuse.get(url)
            #print(f'url: {url}')
            #Check for errors. If "Not Found." continue to next file_path
            try:
                response.raise_for_status()
            except:
                try: 
                    detail = response.json()["detail"]
                except: 
                    error_string = (f'Unknown error. JSON: {response.json()}, ')
                    error_string += (f'Error: {sys.exc_info()[0]}. '
                                        f'{sys.exc_info()[1]}, '
                                    f'line: {sys.exc_info()[2].tb_lineno}')
                    raise Exception(error_string)
                if detail == 'Not found.':
                    #This may happen when script is run against older 
                    # versions of Onefuse that do not support all modules
                    print(f'WARN: policy_type not found: {policy_type},'
                            f' file_path: {file_path}. {file_path} will '
                            f'not be restored')
                    continue
                else: 
                    error_string = (f'Unknown error. JSON: {response.json()}, ')
                    error_string += (f'Error: {sys.exc_info()[0]}. '
                                        f'{sys.exc_info()[1]}, '
                                    f'line: {sys.exc_info()[2].tb_lineno}')
                    raise Exception(error_string)

            response_json = response.json()
            if response_json["count"] == 0:
                print(f'Creating OneFuse Content. policy_type: '
                        f'{policy_type}, file_path: {file_path}')
                url = f'/{policy_type}/'
                restore_content = create_restore_content(json_content,
                                                onefuse,policy_type)
                if policy_type == "moduleCredentials": 
                    restore_content["password"] = "Pl@ceHolder123!"
                    print("WARN: Your credential has been restored but"
                            " before it can be used you must update the "
                            f"password for the credential: {file_path}")
                response = onefuse.post(url,json=restore_content)
                try: 
                    response.raise_for_status()
                except: 
                    error_string = (f'Creation Failed. url: {url}, '
                                    f'restore_content: {restore_content}'
                                    f'Error: {response.content}')
                    raise Exception(error_string)

            elif response_json["count"] == 1:
                print(f'Updating OneFuse Content. policy_type: '
                        f'{policy_type}, file_path: {file_path}')
                policy_json = response_json["_embedded"][policy_type][0]
                policy_id = policy_json["id"]
                url = f'/{policy_type}/{policy_id}/'
                restore_content = create_restore_content(json_content,
                                                onefuse,policy_type)
                response = onefuse.put(url,json=restore_content)
                response.raise_for_status()
            else:    
                err_str = (f'WARN: More than one policy was found with'
                            f' the name: {policy_name} and type: '
                            f'{policy_type}. Skipping policy restore')
                print(err_str)

if __name__ == "__main__":
    main()