import boto3
from botocore.exceptions import ClientError
import json

# Definición de clientes
iam_client = boto3.client('iam')
ses_client = boto3.client('ses')
sm_client = boto3.client('secretsmanager')

# Lista de usuarios a excluir en la rotacion automatica, separados por comas
exclude_users=[""]
# Lista de usuarios a incluir en la rotacion automatica, separados por comas
include_users=[""] 

# Metodo que procesa todos los eventos
def lambda_handler(event, context):
    # Guarda en la var message el mensaje sns como json
    message = json.loads(event['Records'][0]['Sns']['Message'])
    # Parseamos el mensaje hasta obtener el resourceId
    resourceId = message["detail"]
    resourceId = resourceId["newEvaluationResult"]
    resourceId = resourceId["evaluationResultIdentifier"]
    resourceId = resourceId["evaluationResultQualifier"]
    resourceId = resourceId["resourceId"]
 
    # Obtiene el username en funcion del resourceId y lo guarda en la var username
    username = getUser(resourceId)
    # Lista las keys del usuarname obtenido con la funcion de boto3
    keys = iam_client.list_access_keys(UserName=username)

    # Evalua cuantas keys tiene el usuario
    ## Ai tiene 2 keys, guarda la más antigua para eliminarla y guarda la más reciente para deshabilitarla
    if len(keys['AccessKeyMetadata']) == 2:
        d1=keys['AccessKeyMetadata'][0]['CreateDate']
        d2=keys['AccessKeyMetadata'][1]['CreateDate']
        if d1 < d2:
            delete_key=keys['AccessKeyMetadata'][0]
            disable_key=keys['AccessKeyMetadata'][1]
        else:
            delete_key=keys['AccessKeyMetadata'][1]
            disable_key=keys['AccessKeyMetadata'][0]   
    ## Si tiene una sola key, la guarda para deshabilitarla
    else:
        disable_key=keys['AccessKeyMetadata'][0] 
        delete_key=""

    # Desahibilita la key
    disableKey(disable_key)
    # Borra la key
    deleteKey(delete_key)
    # Crea una nueva key para el usuario
    new_key = createKey(username)
    # Obtiene el mail del usuario
    mail = getUserMail(username)

    # Si es la primera vez que rota sus keys automaticamente crea un secreto para almacenar las nuevas keys
    try:
        createSecret(username, new_key)
    # Si no es la primera vez que rota sus keys automaticamente actualiza el secreto con sus nuevas keys
    except Exception as e: 
        updateSecret(username, new_key)

    # Envia un mail al usuario enseñandoles cuales keys fueron deshabilitadas, cuales eliminadas y que vea en Secret Manager su nueva key
    sendMail(mail, username, disable_key, delete_key)

    return resourceId
    
# En base a la función de boto3 list users listamos todos los usuarios de la cuenta
# Entre todos los usuarios busca el que tenga userId igual al resourceid (valor que se trae desde el config)
# Si preferis exlude users poner not in exclude_users en la condicion
def getUser(resourceId):
    response = iam_client.list_users()
    for user in response['Users']:
        # BUSCAR TAGS SIMIL A LA FUNCION DEL MAIL
        if user['UserId'] == resourceId and user['UserName'] in include_users: 
            return user['UserName']
         
# En funcion de la key obtiene el username y la access key y la inactiva
def disableKey(key):
    ak = key['AccessKeyId']
    un = key['UserName']
    
    iam_client.update_access_key(
        AccessKeyId=ak,
        Status='Inactive',
        UserName=un
    )

# En funcion de la key obtiene el username y la access key y la elimina
def deleteKey(key):
    if (key != ""):
        ak = key['AccessKeyId']
        un = key['UserName']
        
        iam_client.delete_access_key(
            AccessKeyId=ak,
            UserName=un
        )
    
# Usando boto3 se crea una nueva key para dicho usuario
def createKey(username):
    response = iam_client.create_access_key(
        UserName=username
    )
    return response
      
# Busca el mail del usuario en el tag mail
def getUserMail(username):
    
    tags = iam_client.list_user_tags(
        UserName=username,
    )
    
    for tag in tags['Tags']:
        if tag['Key'] == 'mail':
            mail = tag['Value']
            return mail

# Crea un secreto para almacenar la nueva key del usuario
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

# Hace update del secret en caso de que este ya existiera
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

# Envia el correo
def sendMail(mail, username, disable_key, delete_key):
    url = "https://console.aws.amazon.com/secretsmanager/home?region=us-east-1#!/listSecrets"
    disable_key = disable_key['AccessKeyId']
    if (delete_key != ""):
        delete_key = delete_key['AccessKeyId']

    SENDER = "sol.malisani@dinocloudconsulting.com" #TODO: change sender
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
