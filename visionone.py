import json
import os
import boto3
import urllib3
import urllib.parse

# Contains a list of Vision One supported regions.
v1SupportedRegions = ["United States", "Europe", "Singapore", "Japan", "Australia", "India"]

# Contains a dictionary of Vision One supported regions and their region-based API Endpoint Base URLs with Region Names as dictionary keys.
v1ApiEndpointBaseUrls = {
    "Australia": "api.au.xdr.trendmicro.com",
    "Europe": "api.eu.xdr.trendmicro.com",
    "India": "api.in.xdr.trendmicro.com",
    "Japan": "api.xdr.trendmicro.co.jp",
    "Singapore": "api.sg.xdr.trendmicro.com",
    "United States": "api.xdr.trendmicro.com"
}

# Returns the Vision One region-based API Endpoint Base URL.
def v1ApiEndpointBaseUrl(v1TrendRegion):

    return "https://" + v1ApiEndpointBaseUrls[v1TrendRegion] + "/beta/xdr/portal"

# Validates the Vision One Auth token passed to this function by listing roles in the Vision One account, returns True if success, otherwise False.
def v1VerifyAuthToken(http, httpHeaders, v1TrendRegion):

    v1ListAccountsResponse = json.loads(http.request('GET', v1ApiEndpointBaseUrl(v1TrendRegion) + "/accounts/roles", headers=httpHeaders).data)    

    if "code" in v1ListAccountsResponse:

        if v1ListAccountsResponse["code"] == "Success":

            return True
    
    return False

# Invites player to the Vision One account via email, assigns a Vision One Role based on the params passed to this function.
def v1InvitePlayer(http, httpHeaders, v1TrendRegion, emailId, v1Role):

    # HTTP Body for the Player Invitation to the Vision One account.
    httpBody = {
        "type": 0,
        "name": str(emailId),
        "enabled": True,
        "description": "Account created by API for Tech Day 2022-1.",
        "token": "",
        "authorization": 3,
        "role": str(v1Role)
    }

    v1InvitePlayerResponse = json.loads(http.request('POST', v1ApiEndpointBaseUrl(v1TrendRegion) + "/accounts/" + urllib.parse.quote_plus(str(emailId)) , headers=httpHeaders, body=json.dumps(httpBody)).data)

    if "error" in v1InvitePlayerResponse:

        print("Error Code: " + str(v1InvitePlayerResponse["error"]["code"]), "Message: ",  str(v1InvitePlayerResponse["error"]["message"]), "-", str(emailId))
    
    elif "code" in v1InvitePlayerResponse:

        if "Success" in v1InvitePlayerResponse["code"]:

            print("Invitation sent to " + str(emailId) + " with role as " + str(v1Role) + ".")

            return True

        else:
            raise Exception('Error: Invitation unsuccessful.')

# Verify User Accounts exist in the Vision One account
def v1VerifyUserAccounts(http, httpHeaders, v1TrendRegion, v1UsersList):

    v1UserAccountsResponse = json.loads(http.request('GET', v1ApiEndpointBaseUrl(v1TrendRegion)  + "/accounts", headers=httpHeaders).data)

    for userAccount in v1UserAccountsResponse["data"]["items"]:

        if userAccount["email"] not in v1UsersList:

            raise Exception('Error: User account not found in the Vision One Account')

        elif not userAccount["enabled"]:

            raise Exception('Error: User account is disabled in the Vision One Account')

    return True

# Retrieve SSM Parameter value based on parameter key passed.
def getV1SsmParameter(ssmClient, paramKey):
    
    parameter = ssmClient.get_parameter(Name='/player/V1/' + paramKey, WithDecryption=True)

    return parameter ['Parameter']['Value']

# Store SSM Parameter key and value on the AWS backend for future use.
def setV1SsmParameter(ssmClient, paramKey, paramValue):
    
    parameter = ssmClient.put_parameter(Name='/player/V1/' + paramKey, Value=paramValue, Type='String', Overwrite=True)

    print(str(parameter))

def main(event, context):

    # Read AWS Lambda Environment variables into the Lambda runtime as variables.
    awsRegion = str(os.environ.get("awsRegion"))
    v1TrendRegion = str(os.environ.get("v1TrendRegion"))    
    v1AuthToken = str(os.environ.get("v1AuthToken"))
    v1UsersList = str(os.environ.get("v1UsersList"))

    # # Invite Player with Role logic
    # v1MasterAdminPlayerEmailList = str(os.environ.get("v1MasterAdminPlayerEmails")).split(",")

    http = urllib3.PoolManager()

    # HTTP Headers for Vision One API calls.
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Authorization": "Bearer " + v1AuthToken
    }

    if v1TrendRegion in v1SupportedRegions:

        # If returns True for Vision One API call, store API Key in AWS SSM Parameter Store for future use.
        if v1VerifyAuthToken(http, headers, v1TrendRegion):

            print("Trend Region - " + str(v1TrendRegion))
            print("Vision One APIs are a Go!!!")

            # Creating an SSM Client to store values in the AWS SSM Parameter Store.
            ssmClient = boto3.client('ssm', region_name=awsRegion)
        
            # Stores global Trend V1 API Base URL as an SSM Parameter  "v1ApiBaseUrl"
            setV1SsmParameter(ssmClient, "v1ApiBaseUrl", v1ApiEndpointBaseUrl(v1TrendRegion))

            # Stores global Trend V1 API Key as an SSM Parameter  "v1ApiKey"
            setV1SsmParameter(ssmClient, "v1ApiKey", v1AuthToken)

            # Verify if all users exist in the Vision One account, raises exception if any one user fails
            if v1VerifyUserAccounts(http, headers, v1TrendRegion, v1UsersList):
                
                print("Success: User(s) exist in the Vision One account")

            else:
                raise Exception('Error: User(s) exists as part of the Vision One account')


            # # Invite player with Master Administrator role onto the Vision One account.
            # for playerEmail in v1MasterAdminPlayerEmailList:

            #     v1InvitePlayer(http, headers, v1TrendRegion, playerEmail, "Master Administrator")
            
    else:
        raise Exception('Error: Invalid Vision One Region')