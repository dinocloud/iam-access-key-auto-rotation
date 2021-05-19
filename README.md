# AWS - Rotacion de Access Key Automatico

## Codigo Python

Logica de la AWS Lambda Function en Python 3.8 para realizar las siguientes acciones:

- Consumir el objecto JSON capturado por la solucion arquitectada con la información del IAM User.
- Evaluar las Access Key del IAM User.
- Eliminar, desactivar o crear nuevas Access Key para los IAM User.
. Crear/Actualizar secretos en AWS Secret Manager para almacenar de forma segura las nuevas credenciales
- Enviar un correo electronico avisando de la rotación de credenciales.

### Logica

Librerias y clientes de boto3 a usar

<img src="/images/libreriasclientes.png" alt="libimg" width="500"/>

Variables para setear los usuarios que se deben incluir/excluir en este proceso

<img src="/images/globalenvs.png" alt="genvs" width="500"/>

Handler de la funcion

<img src="/images/handler.png" alt="handler" width="500"/>

Def getUser

<img src="/images/1getuser.png" alt="gu" width="500"/>

Def disableKey

<img src="/images/2disablekey.png" alt="dk" width="500"/>

Def deleteKey

<img src="/images/3deletekey.png" alt="dtk" width="500"/>

Def createKey

<img src="/images/4createkey.png" alt="ck" width="500"/>

Def getUserMail

<img src="/images/5getuseremail.png" alt="gum" width="500"/>

Def createSecret

<img src="/images/6createsecret.png" alt="cs" width="500"/>

Def updateSecret

<img src="/images/7updatesecret.png" alt="us" width="500"/>

Def sendEmail

<img src="/images/8sendemail.png" alt="se" width="500"/>

## Terraform

Modulo de terraform para deployar una solucion para poder rotar las Access Key de usuarios de IAM de forma automatica.

### Features

- AWS Config Rule ([access-key-rotated](https://docs.aws.amazon.com/config/latest/developerguide/access-keys-rotated.html)).
- AWS CloudWatch Event y Event Rule ([AWS CloudWatch Event](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html)).
- AWS SNS Topic ([AWS SNS Topic](https://docs.aws.amazon.com/sns/latest/dg/welcome.html)).
- AWS Lambda Fuction ([AWS Lambda Fuction](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)).
- AWS IAM Role ([AWS Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)).
- AWS Secret Manager [AWS Secret Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
-Python Code con la logica que va a ejecutar la AWS Lambda Fuction.

### Diagrama de la solucion implementada

Solucion Propuesta:

![solution](/images/Access_Keys_Automated_Rotation.jpg)

1. Se configura una AWS Config Rule que va a estar evaluando de forma periodica la edad de las Access Keys de todos los IAM Users que tengan acceso programatico y tengan un Access Key creada. A la regla vamos a definirle un parametro llamado maxAccessKeyAge con el cual vamos a determinar la cantidad de dias maxima, en numeros enteros, que una Access Key pueden tener de vida (Por ejemplo si seteamos 90 dias las Acces Keys con 91 dias desde su creación van a ser marcadas por la AWS Config Rule). Las Access Key que superen los dias seteados en el parametro van a ser marcados con el estado "Non-Compliant" y las que esten debajo del parametro como "Compliant".

2. Cada vez que la regla evalue genera un objeto JSON con la información del cambio del estado, este objeto JSON lo vamos a capturar con el AWS CloudWatch Event y con la Event Rule que configuramos vamos a filtar solo los cambios de estado de "Compliant" a "Non-Compliant".

3. A AWS CloudWatch Event le vamos a asignar un Target que va a ser nuestro SNS Topic para entregarle el objeto JSON capturado de la AWS Config Rule.

4. El SNS Topic se configura para que triggeree la AWS Lambda Fuction, de esta forma el SNS Topic le va a entregar el objeto JSON a la función con la información que necesita.

5. La AWS Lambda Fuction va a parsear el objeto JSON recibido por el SNS Topic hasta obtener el resourceId del usuario capturado por la AWS Config Rule. El resourceId es un dato que solo podemos ver a nivel programatico o de api call, es un identifier de cada usuario de IAM.

### Terraform Estructura Modulos

```bash
├── environment
│   └── test
│       ├── main.tf
│       └── variables.tf
├── layer
│   └── test
│       ├── access-key-rotation.py
│       ├── main.tf
│       ├── output.tf
│       └── variables.tf
└── aws
    ├── aws_config
    │   ├── main.tf
    │   ├── output.tf
    │   └── variables.tf
    ├── cloudwatch
    │   ├── main.tf
    │   ├── output.tf
    │   └── variables.tf
    ├── lambda
    │   ├── main.tf
    │   ├── output.tf
    │   └── variables.tf
    ├── ses
    │   ├── main.tf
    │   ├── output.tf
    │   └── variables.tf
    └── sns
        ├── main.tf
        ├── output.tf
        └── variables.tf
```

La estrategia implementada en Terraform tiene 3 tiers: 

1. Primer Tier: Denominado bajo la carpeta [aws](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws), vamos a tener declarados nuestros resources.

2. Segundo Tier: Denominado bajo la carpeta [layer](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/layers), vamos a tener declarado la llamada de cada modulo.

3. Tercer Tier: Denominado bajo la carpeta [environment](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/environment/), vamos a tener el modulo de la solucion con todas las llamadas a los modulos definidos en la carpeta [layer](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/layers) que necesitemos para despleglar toda la solucion. Este ultimo tier lo que nos permite es desplegar la infraestructura para cada ambiente, cada capeta que creemos debajo de environment va a ser una instancia de nuestra infraestructura y vamos a poder injectarle distintas variables de entorno para usarla en workloads de dev, stage o prod.


### Requerimientos

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.12.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 3.19 |

### Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 3.19 |

### Modules

| Name | Source |
|------|--------|
| <a name="aws_config"></a> [aws_config](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws/aws_config) | /modules/aws/aws_config 
| <a name="cloudwatch"></a> [cloudwatch](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws/cloudwatch) | /modules/aws/cloudwatch 
| <a name="lambda"></a> [lambda](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws/lambda) | /modules/aws/lambda 
| <a name="ses"></a> [ses](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws/ses) | /modules/aws/ses 
| <a name="sns"></a> [sns](https://github.com/dinocloud/iam-access-key-auto-rotation/tree/master/modules/aws/sns) | /modules/aws/sns 

### Resources

| Name | Type |
|------|------|
| [aws_config_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/config_config_rule) | resource |
| [aws_cloudwatch_event_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_rule.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_lambda_function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_ses_email_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ses_email_identity) | resource |
| [aws_sns_topic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | resource |
| [aws_sns_topic_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) | resource |
| [aws_iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |

