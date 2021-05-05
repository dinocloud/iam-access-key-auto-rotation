import boto3
from botocore.exceptions import ClientError
import datetime
import json

# iniciación de clientes
iam_client = boto3.client('iam')
ses_client = boto3.client('ses')
sm_client = boto3.client('secretsmanager')

# lista de usuarios a excluir en la rotacion automatica
exclude_users=["fsalonia", "validators-app-prod"]

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
    else:
        disable_key=keys['AccessKeyMetadata'][0] 
        delete_key=""

    
    disableKey(disable_key)
    deleteKey(delete_key)

    new_key = createKey(username)

    mail = getUserMail(username)

    try:
        createSecret(username, new_key)
    except Exception as e: 
        updateSecret(username, new_key)

    sendMail(mail, username, disable_key, delete_key)

    return resourceId
    
def getUser(resourceId):
    response = iam_client.list_users()
    
    # entre todos los usuarios busca el que tenga userId igual al resourceid (valor que se trae desde el config)
    for user in response['Users']:
        if user['UserId'] == resourceId and user['UserName'] not in exclude_users: 
            return user['UserName']
         
def disableKey(key):
    ak = key['AccessKeyId']
    un = key['UserName']
    
    iam_client.update_access_key(
        AccessKeyId=ak,
        Status='Inactive',
        UserName=un
    )

def deleteKey(key):
    if (key != ""):
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

    secret_name = "/aws/iam/credentials/" + username

    data = {
        "AccessKey": AccessKeyId,
        "SecretAccessKey": SecretAccessKey
        }

    secret=json.dumps(data)

    sm_client.create_secret(
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


def updateSecret(username, new_key):
    AccessKeyId = new_key['AccessKey']['AccessKeyId']
    SecretAccessKey = new_key['AccessKey']['SecretAccessKey']

    data = {
        "AccessKey": AccessKeyId,
        "SecretAccessKey": SecretAccessKey
        }

    secret=json.dumps(data)

    filter = [ 
        {
            'Key': 'tag-value',
            'Values': [username],
        } ]
    
    list_secret = sm_client.list_secrets(
    MaxResults=1,
    Filters=filter
    )

    secretID = list_secret['SecretList'][0]['ARN']

    sm_client.update_secret  (
        SecretId=secretID,
        Description='Actualizada',
        SecretString=secret
    )


def sendMail(mail, username, disable_key, delete_key):
    url = "https://console.aws.amazon.com/secretsmanager/home?region=us-east-1#!/listSecrets"
    disable_key = disable_key['AccessKeyId']
    if (delete_key != ""):
        delete_key = delete_key['AccessKeyId']

    SENDER = "pedro.bratti@dinocloudconsulting.com"
    CHARSET = "UTF-8"
    SUBJECT = "Sus Access Keys han sido rotadas de forma automática"
    RECIPIENT = mail
       
            
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h3>Username {username}</h3>
    <p><ul>
            <li>Se ha desahibilitado la AccessKeyId: <b>{disable_key}</b></li>
        </ul>
        Visualice su nueva clave en AWS Secret Manager: <a href={url}>{url}</a> através del secreto: <b>/aws/iam/credentials/{username}</b>.
        <br/><br/>
        <i>Este email fue enviado de forma automática a través de Amazon SES</i>.
    </p>
    </body>
    </html>
                """.format(**locals())
    
    
    if (delete_key != ""):
        BODY_HTML = """<html>
        <head></head>
        <body>
        <h3>Username {username}</h3>
        <p><ul>
                <li>Se ha desahibilitado la AccessKeyId: <b>{disable_key}</b></li>
                <li>Se ha eliminado la AccessKeyId: <b>{delete_key}</b></li>
            </ul>
            Visualice su nueva clave en AWS Secret Manager: <a href={url}>{url}</a> através del secreto: <b>/aws/iam/credentials/{username}</b>.
            <br/><br/>
            <i>Este email fue enviado de forma automática a través de Amazon SES</i>.
        </p>
        </body>
        </html>
                    """.format(**locals())
    

    ses_client.send_email(
        Destination={
            'ToAddresses': [
                RECIPIENT,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': CHARSET,
                    'Data': BODY_HTML,
                },
                
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
        },
        Source=SENDER,

    )

def verify_email_identity(email):
    response = ses_client.verify_email_identity(
        EmailAddress=email
    )
    print(response)
