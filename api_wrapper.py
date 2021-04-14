import requests, socket, base64
from requests.auth import HTTPBasicAuth

if __name__ == '__main__':
    import django

    django.setup()

from utilities.models import ConnectionInfo
from utilities.rest import RestConnection

class OneFuseConnector(RestConnection):
    """
    This is a context manager class available to CloudBolt Plugins that
    facilitates easy API connectivity from a CloudBolt host to a OneFuse host
    given the name of a ConnectionInfo object as a string.

    Example:

        from proserv.xui.onefuse_backups.api_wrapper import OneFuseConnector
        with OneFuseConnector("name-of-connection-info-object") as onefuse:
            response = onefuse.get("/namingPolicies/")

    Authentication, headers, and url creation is handled within this class,
    freeing the caller from having to deal with these tasks.

    A boolean parameter called verify_certs with default value of False, is
    provided in the constructor in case the caller wants to enable SSL cert
    validation.

    Installation Instructions: 
    1. Create a Connection Info for onefuse. This must be labelled as 'onefuse'
        - To do this manually from shell plus: 
        > python /opt/cloudbolt/manage.py shell_plus
        > ci = ConnectionInfo(
              name='<name>',
              username='<username>',
              password='<password>',
              ip='<onefuse fqdn>',
              port=<port>,
              protocol='https'
          )
        > ci.labels.add('onefuse')
        > ci.save()

    

    """

    def __init__(self, name: str, verify_certs: bool = None, 
                tracking_id: str = ""):
        if verify_certs == None: 
            verify_certs = False
        if not verify_certs:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try: 
            conn_info = ConnectionInfo.objects.get(
                name__iexact=name,
                labels__name='onefuse'
            )
        except: 
            err_str = (f'ConnectionInfo could not be found with name: {name},'
                       f' and label onefuse')
            raise Exception(err_str)
        self.conn_info = conn_info
        super().__init__(conn_info.username, conn_info.password)
        self.verify_certs = verify_certs
        self.base_url = conn_info.protocol + '://'
        self.base_url += conn_info.ip
        self.base_url += f':{conn_info.port}'
        self.base_url += '/api/v3/onefuse'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Origin-Host': socket.gethostname(),
            'Connection': 'Keep-Alive',
            'SOURCE': 'CLOUDBOLT'
        }
        if tracking_id != None and tracking_id != "":
            self.headers["Tracking-Id"] = tracking_id

    def __enter__(self):
        return self

    def __getattr__(self, item):
        if item == 'get':
            return lambda path, **kwargs: requests.get(
                self.base_url + path,
                auth=HTTPBasicAuth(self.uid,self.pwd),
                headers=self.headers,
                verify=self.verify_certs,
                **kwargs
            )
        elif item == 'post':
            return lambda path, **kwargs: requests.post(
                self.base_url + path,
                auth=HTTPBasicAuth(self.uid,self.pwd),
                headers=self.headers,
                verify=self.verify_certs,
                **kwargs
            )
        elif item == 'delete':
            return lambda path, **kwargs: requests.delete(
                self.base_url + path,
                auth=HTTPBasicAuth(self.uid,self.pwd),
                headers=self.headers,
                verify=self.verify_certs,
                **kwargs
            )
        elif item == 'put':
            return lambda path, **kwargs: requests.put(
                self.base_url + path,
                auth=HTTPBasicAuth(self.uid,self.pwd),
                headers=self.headers,
                verify=self.verify_certs,
                **kwargs
            )
        else:
            return item

    def __repr__(self):
        return 'OneFuseManager'
    
if __name__ == '__main__':
    with OneFuseConnector('onefuse') as onefuse:
        response = onefuse.get('/namingPolicies/')
    import json
    print(json.dumps(response.json(), indent=True))

