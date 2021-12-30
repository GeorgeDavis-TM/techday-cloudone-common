import cfnresponse
import boto3
import os
import base64

def main(event, context):

    print("ResponseURL - " + str(event["ResponseURL"]))
    print("RequestId - " + str(event["RequestId"]))

    regionName = str(os.environ.get("REGION_NAME")) if 'REGION_NAME' in os.environ else None
    functionsList = str(os.environ.get("FUNCTIONS_LIST")) if 'FUNCTIONS_LIST' in os.environ else None

    if functionsList:
        if functionsList[-1] == ", ":
            functionsList = functionsList[:-1].replace(" ", "").split(", ")
        else:
            functionsList = functionsList.replace(" ", "").split(", ")

    if regionName and functionsList:

        lambdaClient = boto3.client('lambda', region_name=regionName)
        
        lambdaBundledResponse = {}

        for functionName in functionsList:

            print("Triggered - " + str(functionName))

            lambdaFunctionInvokeResponse = lambdaClient.invoke(
                FunctionName=functionName, InvocationType='RequestResponse', LogType='Tail')

            tempDict = {lambdaFunctionInvokeResponse["ResponseMetadata"]["RequestId"]: {"StatusCode": lambdaFunctionInvokeResponse["StatusCode"], "LogResult": base64.b64decode(lambdaFunctionInvokeResponse["LogResult"]).decode("utf-8")}}

            lambdaBundledResponse.update(tempDict)

        responseObj = { "Output": lambdaBundledResponse }

        for item in responseObj["Output"]:

            if "LogResult" in responseObj["Output"][item]:

                responseObj["Output"][item].pop("LogResult")

        for lambdaResponseItem in lambdaBundledResponse:

            if str(lambdaBundledResponse[lambdaResponseItem]["StatusCode"]) != "200":

                cfnresponse.send(event, context, cfnresponse.FAILED, responseObj)

            elif str(lambdaBundledResponse[lambdaResponseItem]["StatusCode"]) == "200":

                if "ERROR" in str(lambdaBundledResponse[lambdaResponseItem]["LogResult"]):

                    print("ERROR: ", str(lambdaBundledResponse[lambdaResponseItem]["LogResult"]))

                    cfnresponse.send(event, context, cfnresponse.FAILED, responseObj)

        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseObj)

    else:

        responseObj = { "Output": "Environment variables are set or parsed incorrectly." }
        
        cfnresponse.send(event, context, cfnresponse.FAILED, responseObj)
