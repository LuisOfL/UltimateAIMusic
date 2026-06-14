import boto3
import hmac
import hashlib
import base64
from fastapi import HTTPException

# Configuración
COGNITO_CLIENT = boto3.client('cognito-idp', region_name='us-east-2')
CLIENT_ID = '7u2c6fkvotf6enh7hhftsstu1b'
CLIENT_SECRET = '1lqkfh08csgocf76pnf92u66mdp46ibvmsmiok07dqgdpkcnsike' # Si no tienes, deja esto como None

def get_secret_hash(username):
    if not CLIENT_SECRET:
        return None
    message = username + CLIENT_ID
    dig = hmac.new(
        str(CLIENT_SECRET).encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def registrar_usuario(email, password, username, birthdate, country, state):
    try:
        kwargs = {
            'ClientId': CLIENT_ID,
            'Username': email,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email', 'Value': email},
                {'Name': 'preferred_username', 'Value': username},
                {'Name': 'birthdate', 'Value': birthdate},
                {'Name': 'custom:country', 'Value': country},
                {'Name': 'custom:state', 'Value': state}
            ]
        }
        
        # Si existe secreto, añadimos el SecretHash
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['SecretHash'] = secret_hash

        COGNITO_CLIENT.sign_up(**kwargs)
        return {"message": "Usuario registrado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def iniciar_sesion(email, password):
    try:
        kwargs = {
            'ClientId': CLIENT_ID,
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': email,
                'PASSWORD': password
            }
        }
        
        secret_hash = get_secret_hash(email)
        if secret_hash:
            kwargs['AuthParameters']['SECRET_HASH'] = secret_hash

        response = COGNITO_CLIENT.initiate_auth(**kwargs)
        return response['AuthenticationResult']
    except Exception as e:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")