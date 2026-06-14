import boto3
import hmac
import hashlib
import base64
from fastapi import HTTPException
import psycopg2

# Configuración
COGNITO_CLIENT = boto3.client('cognito-idp', region_name='us-east-2')
CLIENT_ID     = '7u2c6fkvotf6enh7hhftsstu1b'
CLIENT_SECRET = '1lqkfh08csgocf76pn*************ke'
USER_POOL_ID  = 'us-east-2_8yKinp7Md'  

DB_HOST = "seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com"
DB_NAME = "Users"
DB_USER = "postgres"
DB_PASS = "Nome******"


def get_secret_hash(username):
    if not CLIENT_SECRET:
        return None
    message = username + CLIENT_ID
    dig = hmac.new(
        str(CLIENT_SECRET).encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def registrar_usuario(email, password, username, birthdate, country, state):
    try:
        # 1. Registro inicial en Cognito
        kwargs = {
            'ClientId': CLIENT_ID,
            'Username': email,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email',               'Value': email},
                {'Name': 'preferred_username',  'Value': username},
                {'Name': 'birthdate',           'Value': birthdate},
                {'Name': 'custom:country',      'Value': str(country)},
                {'Name': 'custom:state',        'Value': str(state)},
            ],
        }
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['SecretHash'] = secret_hash

        # Registrar en Cognito
        sign_up_res = COGNITO_CLIENT.sign_up(**kwargs)
        # Obtenemos el UUID único (UserSub) que Cognito le asigna al usuario
        cognito_id = sign_up_res['UserSub'] 

        # 2. Confirmación automática en Cognito
        COGNITO_CLIENT.admin_confirm_sign_up(
            UserPoolId=USER_POOL_ID,
            Username=email,
        )

        # 3. Forzar verificación de email en Cognito
        COGNITO_CLIENT.admin_update_user_attributes(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[{'Name': 'email_verified', 'Value': 'true'}],
        )

        print(f"Usuario {email} confirmado exitosamente en Cognito. Iniciando inserción en RDS...")

        # 4. Inserción directa en PostgreSQL (Sincronizado)
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=5
        )
        cur = conn.cursor()
        
        # Query idéntico a las columnas de tu pgAdmin
        query = """INSERT INTO usuarios (cognito_id, email, username, birthdate, country, state) 
                   VALUES (%s, %s, %s, %s, %s, %s);"""
        
        cur.execute(query, (
            cognito_id,  # El UUID real generado por Cognito
            email, 
            username, 
            birthdate, 
            country, 
            state
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"¡Usuario {email} guardado con éxito en la base de datos Users!")

        return {"message": "Usuario registrado exitosamente"}

    except COGNITO_CLIENT.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    except COGNITO_CLIENT.exceptions.InvalidPasswordException:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 caracteres, una mayúscula, un número y un símbolo"
        )
    except Exception as e:
        print(f"Error en registro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=f"Error en el proceso de registro: {str(e)}")


def iniciar_sesion(email, password):
    try:
        kwargs = {
            'ClientId': CLIENT_ID,
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': email,
                'PASSWORD': password,
            },
        }
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['AuthParameters']['SECRET_HASH'] = secret_hash

        response = COGNITO_CLIENT.initiate_auth(**kwargs)
        return response['AuthenticationResult']

    except COGNITO_CLIENT.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    except COGNITO_CLIENT.exceptions.UserNotFoundException:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    except Exception as e:
        print(f"Error en login: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Error al iniciar sesión")
