#!/usr/bin/python

# Python version of mda515t\folio\Folioapi3 php class
# from mst but with Request sessions
import time
from requests import Session
from requests.exceptions import HTTPError
from getpass import getpass
import uuid
import configparser
import logging
import json

# FolioApi class
class FolioApi():

    # Class Variables
    namespace = uuid.UUID('8405ae4d-b315-42e1-918a-d1919900cf3f')

    okapi_token = ''
    tenant = ''
    okapi_url = ''
    
    moveit_host = ''
    moveit_user = ''
    moveit_pw = ''

    email_sender = ''
    email_recipient = ''
    email_server = ''

    default_headers = {
        'x-okapi-tenant': tenant,
        'x-okapi-token': okapi_token
    }

    timeout = 10
    retries = 10
    retryMultiplier = 1.5
    lastQuery = ''
    lastCode = ''
    lastResponse = ''
    session = Session()
    session.headers = default_headers
    #### Class Methods ####

    # Constructor method
    def __init__(self, filepath: str='src/config/config.ini'):
        self.setupConfig(filepath)
        if not self.okapi_token:
            _okapi_token = self.getToken()
            self.setToken(_okapi_token)
            self.updateConfig(filepath, 'folioapi', 'okapi_token', _okapi_token)

    def setupConfig(self, filepath: str):
        config = configparser.ConfigParser()
        config.read(filepath)

        self.okapi_token = config.get("folioapi", "okapi_token")
        self.tenant = config.get("folioapi", "tenant")
        self.okapi_url = config.get("folioapi", "okapi_url")

        self.moveit_host = config.get("moveit", "host")
        self.moveit_user = config.get("moveit", "username")
        self.moveit_pw = config.get("moveit", "password")

        self.email_server = config.get("bursaremails", "smtp_server")
        self.email_sender = config.get("bursaremails", "sender")
        self.email_recipient = config.get("bursaremails", "recipient")
        
        self.default_headers = {
            'x-okapi-tenant': self.tenant,
            'x-okapi-token': self.okapi_token
        }
        self.session.headers.update(self.default_headers)
        
    def updateConfig(self, file, section, system, value):
        config = configparser.ConfigParser()
        config.read(file)
        cfgfile = open(file, 'w')
        config.set(section, system, value)
        config.write(cfgfile)
        cfgfile.close()

    def preStage(self, endpoint):
        self.getToken()
        self.lastQuery = ''
        self.lastCode = ''
        self.lastResponse = ''
        self.lastHeaders = []
        return str(endpoint).strip('/')

    def _delete(self, endpoint, id):
        try:
            endpoint = self.preStage(endpoint)
            url = self.okapi_url + str(endpoint) + "/" + str(id)
            print("DELETE url: " + url)
            with self.session.delete(url, headers=self.default_headers) as resp:
                resp.raise_for_status()
                if resp.status_code == 204:
                    print("Deleted successfully")
                if resp.content:
                    return json.loads(resp.content)
                else:
                    return None
        except Exception as e:
            print(e)

    def get(self, endpoint, params=[], id=None):
        try:
            endpoint = self.preStage(endpoint)
            p = ''
            if params:
                p='?'
                for param in params:
                    p = p + str(param) + "=" + str(params[param]) + "&"
                p = p[0:-1]
            if id:
                endpoint = endpoint + "/" + str(id)
            endpoint = endpoint + p
            url = self.okapi_url + "/" + endpoint
            # print("GET url: " + url)
            with self.session.get(url) as resp:
                resp.raise_for_status()
                return json.loads(resp.content)
        except HTTPError as httpError:
            logging.debug(httpError)
        except Exception as e:
            print(e)

    def _post(self, endpoint, data=[], options=[]):
        try:
            endpoint = self.preStage(endpoint)
            url = self.okapi_url + endpoint
            headers = self.default_headers
            print("POST url: " + url)
            if data:
                print("data: " + str(data))
            if options:
                print("options: " + str(options))
                if 'headers' in options:
                    h = options['headers']
                    for key in h:
                        print(key + ": " + h[key])
                        headers[key] = h[key]
            print("headers: " + str(headers))
            with self.session.post(url, headers=headers, json=data) as resp:
                resp.raise_for_status()
                if resp.status_code == 204:
                    print("Response code: 204 OK")
                if resp.content:
                    return json.loads(resp.content)
                else:
                    return None
        except Exception as e:
            print(e)

    def setToken(self, token):
        self.okapi_token = token
        
    def getToken(self):
        if self.okapi_token:
            return self.okapi_token
        else:
            try:
                username = input("Username?: ")
                password = getpass()
                payload = {
                    "tenant": self.tenant,
                    "username": username,
                    "password": password
                }
                url = self.okapi_url + "/authn/login"
                headers = {
                    "Content-type": "application/json",
                    "X-Okapi-Tenant": self.tenant
                }
                with self.session.post(url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    okapi_token = resp.headers['x-okapi-token']
                    print(okapi_token)
                    return okapi_token
            except Exception as e:
                print("Could not get token.")
                print(e)

    # def rawRequest(self, verb, endpoint, headers, payload):
    #     tryNum = 0
    #     prevTimeout = self.timeout
    #     print("prevTimeout: " + str(prevTimeout))
    #     ## Do not exceed max number of requests
    #     while tryNum < self.retries:
    #         timeout = round((prevTimeout * self.retryMultiplier) * 100) / 100
    #         print("timeout: " + str(timeout))
    #         prevTimeout = timeout
    #         print("prevTimeout: " + str(prevTimeout))
    #         if tryNum > 0:
    #             print("Retry: " + str(tryNum) + "\n")
    #         try:
    #             response = self.session.request(verb, endpoint, headers=headers, json=payload)
    #             print(response.text)
    #             keys = options.keys()
    #             print("keys: " + keys)
    #             if 'json' in keys:
    #                 self.lastQuery = str(verb) + ": " + self.okapi_url + str(endpoint) + " params:" + json.dumps(options['json'])
    #             else:
    #                 self.lastQuery = str(verb) + ": " + self.okapi_url + str(endpoint)
                
    #             self.lastCode = str(response.status_code)
    #             self.lastHeaders = response.headers
    #             self.lastResponse = str(response.content)
    #             if response:
    #                 return response
    #             else:
    #                 return None
    #         except ConnectionError as e:
    #             tryNum += 1
    #             time.sleep((250 / 1000000))
    #             if (tryNum >= self.retries):
    #                 print("Retries exceeded: " + e.strerror + " endpoint: " + str(endpoint) + "\n")
    #             else:
    #                 print("Connect Exception: " + e.strerror + " endpoint: " + str(endpoint) + "\n")

    def newFileDefinition(self, filename: str):
        try:
            payload = {}
            payload['fileName'] = filename
            response = self.post('/data-export/file-definitions', data=payload)
            if response:
                return response
            else:
                return None
        except Exception as e:
            print(e)


    def uploadFileDefinition(self, filename: str, fileDefinitionId):
        try:
            options = {}
            options['headers'] = {
                'Content-type': 'application/octet-stream'
            }
            with open(filename, 'r') as file:
                lines = file.read()
            response = self.post('/data-export/file-definitions/' + fileDefinitionId + '/upload', data=lines, options=options)
            if response:
                return response
            else:
                return None
        except Exception as e:
            print(e)
        pass


    def getJobExecutionById(self, jobExecutionId):
        try:
            options = {}
            options['query'] = '(id==' + str(jobExecutionId) + ')'
            response = self.get('/data-export/job-executions', params=options)
            if response:
                return response
            else:
                return None
        except Exception as e:
            print(e)


    def _export(self, filename: str):
        ### filename: File must be one of: a) csv, with one uuid per line, or b) cql query file
        try:
            ## res is the json obect representing a newly created fileDefinition
            fileDefinition = self.newFileDefinition(filename)
            print("fileDefinition: " + str(fileDefinition))
            ## Grab the fileDefinitionId and the jobExecutionId
            fileDefinitionId = fileDefinition['id']
            print("fileDefinitionId: " + str(fileDefinitionId))
            jobExecutionId = fileDefinition['jobExecutionId']
            print("jobExecutionId: " + str(jobExecutionId))
            ## method for uploading file to folio
            uploadResponse = self.uploadFileDefinition(filename, fileDefinitionId)
            print(uploadResponse)
            ## res Will return status code of 204 with success. 'Kicks off' jobExecution
            jobProfileId = "6f7f3cd7-9f24-42eb-ae91-91af1cd54d0a"
            payload = {
                "jobProfileId": jobProfileId,
                "fileDefinitionId": fileDefinitionId,
                "idType": "instance"
            }
            res = self.post('data-export/export', data=payload)
            ## wait a few seconds for initial upload to process
            time.sleep(3)
            ## getJobExecutionById will return the matching job execution object for given jobExecutionId
            jobExecution = self.getJobExecutionById(jobExecutionId)
            print("jobExecution: " + str(jobExecution))
            status = jobExecution['jobExecutions'][0]['status']
            print("status: " + str(status))
            while status != 'COMPLETE':
                time.sleep(1)
                jobExecution = self.getJobExecutionById(jobExecutionId)
                status = jobExecution['jobExecutions'][0]['status']
                print("Status: " + str(status))
            print(res)
        except Exception as e:
            print(e)
        
    ### getMarcRecordIdentifiers: 
    # Returns a list of recordIds returned by MARC Search Query API (see payload)
    def getMarcRecordIdentifiers(self, leaderSearch=None, fieldsSearch=None, offset=0, limit=10):
        recordIds = []
        url = "https://okapi-umsystem.folio.ebsco.com/source-storage/stream/marc-record-identifiers"
        if leaderSearch and not fieldsSearch:
            payload = {
                "leaderSearchExpression": leaderSearch,
                "limit": limit,
                "offset": offset
            }
        elif fieldsSearch and not leaderSearch:
            payload = {
                "fieldsSearchExpression": fieldsSearch,
                "limit": limit,
                "offset": offset
            }
        elif fieldsSearch and leaderSearch:
            payload = {
                "leaderSearchExpression": leaderSearch,
                "fieldsSearchExpression": fieldsSearch,
                "limit": limit,
                "offset": offset
            }
        else:
            print("1 or more of leaderSearch or fieldsSearch must be provided.")
            return
        headers = self.default_headers
        headers['Content-type'] = 'application/json'
        try:
            # POST request to /marc-record-identifiers to get back an array of record uuids
            response = self.session.post(url, headers=headers, json=payload)
            if response.ok:
                records = response.json()
                total_count = records['totalCount']
                print("Records returned: " + str(total_count))
                recordIds.extend(records['records'])
                offset += limit
                while offset <= total_count:
                    print("offset: " + str(offset) + "/" + str(total_count))
                    payload['offset'] = offset
                    response = self.session.post(url, headers=headers, json=payload)
                    if response.ok:
                        records = response.json()
                        recordIds.extend(records['records'])
                        offset += limit
            return recordIds
        except Exception as e:
            print(e)
            time.sleep(5)


    def getTextInstancesUuids(self, uuid_list):
        text_uuids = []
        for instance_uuid in uuid_list:
            # GET instance JSON from FOLIO
            url = "https://okapi-umsystem.folio.ebsco.com/instance-storage/instances/" + instance_uuid
            payload = ''
            try:
                response = self.session.get(url, headers=self.default_headers, data=payload)
                if not response.ok:
                    print(response.reason)
                    print(response.text)
                if response.ok:
                    response_json = response.json()
                    print(response_json)
                    # GET Instance and grab the instanceType
                    instance_type = response_json['instanceTypeId']
                    print(instance_type)
                    # if instance type equals text then add to text_uuids
                    if instance_type == "6312d172-f0cf-40f6-b27d-9fa8feaf332f":
                        text_uuids.append(instance_uuid)
                
                return text_uuids
            except Exception as e:
                print(e)
                time.sleep(5)


    def getLocationInstanceIds(self, loc_uuid, get_only_unsuppressed=True): # returns list of instanceIds for given location (loc_uuid)
        offset = 0
        limit = 250
        instanceIds = []
        instanceIdsFin = []
        # GET all holdings records from a location and grab their instanceIds
        if get_only_unsuppressed:
            query = 'discoverySuppress==false and effectiveLocationId==' + loc_uuid
        else:
            query = 'effectiveLocationId==' + loc_uuid
        url = "https://okapi-umsystem.folio.ebsco.com/holdings-storage/holdings?offset=" + str(offset) + "&limit=" + str(limit) + "&query=(" + query + ")"
        try:
            response = self.session.get(url, headers=self.default_headers)
            if not response.ok:
                print(response.reason)
                print(response.text)
            if response.ok:
                holdings_records = response.json()
                # logging.info(holdings_records)
                total_records = holdings_records['totalRecords']
                print("# of records for location " + str(loc_uuid) + ": " + str(total_records))
                print("API calls to get all items: " + str(int(total_records / limit) + 1) + "...")
                for record in holdings_records['holdingsRecords']:
                    instanceIds.append(record['instanceId'])
                # logging.info(instanceIds)
                offset += limit
                while offset <= total_records:
                    # print("------> offset: " + str(offset))
                    url = "https://okapi-umsystem.folio.ebsco.com/holdings-storage/holdings?offset=" + str(offset) + "&limit=" + str(limit) + "&query=(" + query + ")"
                    response = self.session.get(url, headers=self.default_headers)
                    if not response.ok:
                        print(response.reason)
                        print(response.text)
                    if response.ok:
                        holdings_records = response.json()
                        for record in holdings_records['holdingsRecords']:
                            instanceIds.append(record['instanceId'])
                        offset += limit
                # logging.info(str(len(instanceIds)))
                return instanceIds
        except Exception as e:
            print(e)
            time.sleep(5)

    def getInstancebyId(self, instance_uuid): # returns Instance Json object
        # GET instance JSON from FOLIO
        url = "https://okapi-umsystem.folio.ebsco.com/instance-storage/instances/" + instance_uuid
        payload = ''
        try:
            response = self.session.get(url, headers=self.default_headers, data=payload)
            if not response.ok:
                print(response.reason)
                print(response.text)
            if response.ok:
                response_json = response.json()
                return(response_json)
        except Exception as e:
            print(e)
            time.sleep(5)
    

    def quickExport(self, recordUuids): # recordUuids is a list of records to export. Returns a jobExecutionId (uuid)
        # POST request to /data-export/quick-export to get jobExecutionId with list of record uuids as part of request body
        url = "https://okapi-umsystem.folio.ebsco.com/data-export/quick-export"
        payload = {
            "uuids": recordUuids,
            "type": "uuid",
            "recordType": "INSTANCE"
        }
        headers = {
            'x-okapi-tenant': self.tenant,
            'x-okapi-token': self.okapi_token,
            'Content-type': 'application/json'          
        }
        try:
            response = self.session.post(url, headers=headers, json=payload)
            response_json = response.json()
            print(response_json)
            jobId = response_json['jobExecutionId']

            return jobId
        except Exception as e:
            print(e)
            time.sleep(5)

    def getHoldingsByInstanceId(self, instance_id): # Returns an array of Holdings json records
        query = '?query=(instanceId=="' + instance_id + '")'
        url = "https://okapi-umsystem.folio.ebsco.com/holdings-storage/holdings" + query
        try:
            response = self.session.get(url, headers=self.default_headers)
            holdingsRecords = response.json()['holdingsRecords']
            
            return holdingsRecords
        except Exception as e:
            print(e)
            time.sleep(5)

    def dumpHoldings(self, offset=0, limit=10):
        url = "https://okapi-umsystem.folio.ebsco.com/holdings-storage/holdings"
        try:
            response = self.session.get(url, headers=self.default_headers)
            holdingsRecords = response.json()

            return holdingsRecords
        except Exception as e:
            print(e)
            time.sleep(5)

    def postFileDefinition(self, filename):
        url = self.okapi_url + "/data-export/file-definitions"
        payload = {
            "fileName": filename
        }
        ### send POST request to /data-export/file-definitions with payload containing csv filename
        try:
            response = self.session.post(url, headers=self.default_headers, json=payload)
            fileDefinition = response.json()

            return fileDefinition
        except Exception as e:
            print(e)
            time.sleep(5)

    def uploadFile(self, fileDefId, fileObject): # the list of uuids is one per line with '\n' separating each record
        ### send POST request to /data-export/file-definitions/{fileDefinitionId}/upload
        url = self.okapi_url + "/data-export/file-definitions/" + str(fileDefId) + "/upload"
        headers = self.default_headers
        headers['Content-type'] = 'application/octet-stream'
        try:
            response = self.session.post(url, headers=headers, data=fileObject)
            response_json = response.json()

            return response_json
        except Exception as e:
            print(e)
            time.sleep(5)

    def startExport(self, jobProfileId, fileDefinitionId, idType="instance"): # idType enum: {"instance", "holding", }
        ### send POST request to /data-export/export with json body
        url = self.okapi_url + "data-export/export"
        payload = {
            "jobProfileId": jobProfileId,
            "fileDefinitionId": fileDefinitionId,
            "idType": idType
        }
        try:
            response = self.session.post(url, headers=self.default_headers, json=payload)
            if not response.ok:
                print(response.reason)
                print(response.text)
            if response.status_code == 204:
                print("Success")
        except Exception as e:
            print(e)
            time.sleep(5)
        pass


    def getLocations(self, limit=500):
        try:
            url = F"{self.okapi_url}/locations"
            params ={}
            params['limit'] = limit
            resp = self.session.get(url, headers=self.default_headers, params=params)
            if resp:
                if resp.ok:
                    return resp.json()
            else:
                return None
        except Exception as e:
            print(e)

    def searchInstances(self, query='cql.allRecords=1', expandAll=True, offset=0, limit=10):
        try:
            url = self.okapi_url + '/search/instances'
            params = {}
            params['query'] = query
            params['expandAll'] = expandAll
            params['offset'] = offset
            params['limit'] = limit
            resp = self.session.get(url, headers=self.default_headers, params=params)
            if resp:
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(e)

    def getInstanceIds(self, query):
        try:
            url = self.okapi_url + "/search/instances/ids"
            params = {}
            params['query'] = query
            resp = self.session.get(url, headers=self.default_headers, params=params)
            if resp:
                print(str(resp.status_code))
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print("getInstanceIds() Exception")
            print(e)

### getHoldingsIds: Get a list of holding ids linked to instances found by the CQL query
##    Parameters: query <required>: A CQL query string with search conditions.
    def getHoldingIds(self, query: str):
        try:
            url = self.okapi_url + '/search/holdings/ids'
            params = {}
            params['query'] = query
            resp = self.session.get(url, headers=self.default_headers, params=params)
            if resp:
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(e)

    ### Gets all locations and returns them as an array of json Objects
    ### *All of the following limits ->(Assumes there are not more than 9999 of the given objects)
    def getAllLocations(self, limit=9999):
        try:
            _params = {'limit': limit}
            resp = self.session.get(self.okapi_url+'/locations', params=_params)
            if resp.ok:
                locations = resp.json()['locations']
                return locations
        except Exception as e:
            print(e)

    # Returns a list of service points, service_points
    def getServicePoints(self, _limit=9999) -> list:
        try:
            service_points = []
            params = {'limit': _limit}
            servicePoints = self.get('service-points', params=params)
            if servicePoints:
                service_points = servicePoints['servicepoints']
            return service_points
        except Exception as e:
            print(e)
    
    # Returns a list of user groups, _usergroups
    def getUserGroups(self, _limit=9999) -> list:
        try:
            _usergroups = []
            params = {'limit': _limit}
            groups = self.get('groups', params=params)
            if groups:
                _usergroups = groups['usergroups']
            return _usergroups
        except Exception as e:
            print(e)

    #######################################
    # Get totalRecords returned for query #
    #######################################
    def getTotalRecords(self, endpoint: str, query=None):
        try:
            if query != None:
                params = {"limit": 0, "offset": 0, "query": query}
            else:
                params = {"limit": 0, "offset": 0}

            totalRecords = self.get(endpoint, params=params)['totalRecords']
            return totalRecords
        except Exception as e:
            logging.debug(F"endpoint: {endpoint}, params: {params} -> Exception: {e}")