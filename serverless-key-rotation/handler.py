import boto3
from botocore.exceptions import ClientError
import datetime
import json
import urllib3

# inicia el cliente de iam
iam_client = boto3.client('iam')
ses_client = boto3.client('ses')
sm_client = boto3.client('secretsmanager')

# lista de usuarios a excluir en la rotacion automatica
exclude_users=["fsalonia", "validators-app-prod"]

event = {
    "version": "0",
    "id": "c0bb891c-77fe-8518-14fc-be78b966f95b",
    "detail-type": "Config Rules Compliance Change",
    "source": "aws.config",
    "account": "477575873490",
    "time": "2021-04-19T19:04:05Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
        "resourceId": "AIDAW6MN5QPJPMC7R4QBE",
        "awsRegion": "us-east-1",
        "awsAccountId": "477575873490",
        "configRuleName": "access-keys-rotated",
        "recordVersion": "1.0",
        "configRuleARN": "arn:aws:config:us-east-1:477575873490:config-rule/config-rule-eguym2",
        "messageType": "ComplianceChangeNotification",
        "newEvaluationResult": {
            "evaluationResultIdentifier": {
                "evaluationResultQualifier": {
                    "configRuleName": "access-keys-rotated",
                    "resourceType": "AWS::IAM::User",
                    "resourceId": "AIDAW6MN5QPJPMC7R4QBE"
                },
                "orderingTimestamp": "2021-04-19T19:03:50.251Z"
            },
            "complianceType": "NON_COMPLIANT",
            "resultRecordedTime": "2021-04-19T19:04:04.741Z",
            "configRuleInvokedTime": "2021-04-19T19:04:04.332Z"
        },
        "oldEvaluationResult": {
            "evaluationResultIdentifier": {
                "evaluationResultQualifier": {
                    "configRuleName": "access-keys-rotated",
                    "resourceType": "AWS::IAM::User",
                    "resourceId": "AIDAW6MN5QPJPMC7R4QBE"
                },
                "orderingTimestamp": "2021-04-19T19:02:33.749Z"
            },
            "complianceType": "COMPLIANT",
            "resultRecordedTime": "2021-04-19T19:02:44.919Z",
            "configRuleInvokedTime": "2021-04-19T19:02:44.583Z"
        },
        "notificationCreationTime": "2021-04-19T19:04:05.751Z",
        "resourceType": "AWS::IAM::User"
    }
}

def lambda_handler(event, context):
    # message = json.loads(event['Records'][0]['Sns']['Message'])
    # resourceId = message["detail"]
    # resourceId = resourceId["newEvaluationResult"]
    # resourceId = resourceId["evaluationResultIdentifier"]
    # resourceId = resourceId["evaluationResultQualifier"]
    # resourceId = resourceId["resourceId"]
    resourceId = "AIDAW6MN5QPJPMC7R4QBE"
 
    username = getUser(resourceId)
    keys = iam_client.list_access_keys(UserName=username)

    if len(keys['AccessKeyMetadata']) == 2:
        d1=keys['AccessKeyMetadata'][0]['CreateDate']
        d2=keys['AccessKeyMetadata'][1]['CreateDate']
        if d1 < d2:
            delete_key=keys['AccessKeyMetadata'][0]
            disable_key=keys['AccessKeyMetadata'][1]
        else:
            delete_key=keys['AccessKeyMetadata'][1]
            disable_key=keys['AccessKeyMetadata'][0]   
        deleteKey(delete_key)
    else:
        disable_key=keys['AccessKeyMetadata'][0] 

    
    disableKey(disable_key)
    new_key = createKey(username)

    mail = getUserMail(username)

    createSecret(username, new_key)

    sendMail(mail, username, new_key, disable_key, delete_key)

    return resourceId
    
def getUser(resourceId):
    response = iam_client.list_users()
    
    # entre todos los usuarios busca el que tenga userId igual al resourceid (valor que se trae desde el config)
    for user in response['Users']:
        if user['UserId'] == resourceId and user['UserName'] not in exclude_users: 
            return user['UserName']
            
def listKeys(username, keys):     
    # si el usuario tiene mas de una access key borra la mas antigua y deshabilita la otra
    if len(keys['AccessKeyMetadata']) == 2:
        d1=keys['AccessKeyMetadata'][0]['CreateDate']
        d2=keys['AccessKeyMetadata'][1]['CreateDate']
        if d1 < d2:
            delete_key=keys['AccessKeyMetadata'][0]
            disable_key=keys['AccessKeyMetadata'][1]
        else:
            delete_key=keys['AccessKeyMetadata'][1]
            disable_key=keys['AccessKeyMetadata'][0]
        
        return disable_key, delete_key
        # # desabilitar la key existe mas reciente
        # disableKey(disable_key)
        # # borrar key mas vieja
        # deleteKey(delete_key)
        # # create new key
        # createKey(username)
        
    else:
        disable_key=keys['AccessKeyMetadata'][0] # en el caso q tenga una sola esta siempre va a ser la vieja
        # disable old key
        # disableKey(oldKey)
        # create new key
        # createKey(username)
        return disable_key
    
def disableKey(key):
    ak = key['AccessKeyId']
    un = key['UserName']
    
    iam_client.update_access_key(
        AccessKeyId=ak,
        Status='Inactive',
        UserName=un
    )

def deleteKey(key):
    ak = key['AccessKeyId']
    un = key['UserName']
    
    iam_client.delete_access_key(
        AccessKeyId=ak,
        UserName=un
    )
    
def createKey(username):
    response = iam_client.create_access_key(
        UserName=username
    )
    return response
      
# busca el mail del usuario en el tag mail
def getUserMail(username):
    
    tags = iam_client.list_user_tags(
        UserName=username,
    )
    
    for tag in tags['Tags']:
        if tag['Key'] == 'mail':
            mail = tag['Value']
            return mail

def createSecret(username, new_key):
    AccessKeyId = new_key['AccessKey']['AccessKeyId']
    SecretAccessKey = new_key['AccessKey']['SecretAccessKey']

    secret_name = "Access_keys9_" + username
    # secret="'{'AccessKeyId':" + AccessKeyId + ",'SecretAccessKey':" + SecretAccessKey + "}'"
   
    # secret={"AccessKeyId":AccessKeyId,"SecretAccessKey":SecretAccessKey}
    # secret = urllib3.quote("'{}'".format(secret))

    secret='{"username":f'"{AccessKeyId}"',"password":"BnQw!XDWgaEeT9XGTT29"}'

    response = sm_client.create_secret(
        Name=secret_name,
        Description='New Access Keys',
        SecretString=secret,
        Tags=[
            {
                'Key': 'Owner',
                'Value': username
            },
        ],
    )

    print(response)

def sendMail(mail, username, new_key, disable_key, delete_key):

    BODY_TEXT = "Hubo una rotación en las Access Keys del usuario: " + username + "\r\n" + "Se desahibilitó la AccessKeyId: " + disable_key['AccessKeyId'] +  "\r\n" + "Y se elimino la AccessKeyId: " + delete_key['AccessKeyId'] + "\r\n \r\n Sus nuevas credenciales son: \r\n" + new_key['AccessKey']['AccessKeyId'] + "\r\n" + new_key['AccessKey']['SecretAccessKey'] + "\r\n \r\n \r\n Este email fue enviado de forma automática a través de Amazon SES."
            
    ses_client.send_email(
    Source='sol.malisani@dinocloudconsulting.com',
    Destination={
        'ToAddresses': [
            mail,
        ]
    },
    Message={
        'Subject': {
            'Data': 'Renovación de keys'
        },
        'Body': {
            'Text': {
                'Data': BODY_TEXT
            }
        }
    }
)

def verify_email_identity(email):
    response = ses_client.verify_email_identity(
        EmailAddress=email
    )
    print(response)
