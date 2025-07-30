import uuid
from datetime import datetime, timezone, timedelta

from jose import jwt, JWTError


from src.shared.config import get_auth_data


async def create_token(data: dict, token_type: str = "access"):
    auth_data = await get_auth_data()
    expire = datetime.now(timezone.utc) + timedelta(minutes=auth_data["expire_access"])
    to_encode = data.copy()
    returning_data = {}
    if token_type == "access":
        to_encode.update({"exp": expire, "type": "access"})
    elif token_type == "refresh":
        expire = datetime.now(timezone.utc) + timedelta(minutes=auth_data["expire_refresh"])
        token_id = str(uuid.uuid4())
        to_encode.update({
            "exp": expire,
            "jti": token_id,
            "type": "refresh"})
        returning_data.update({"token_id": token_id})
    else:
        return None
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    returning_data.update({"token": encode_jwt})
    return returning_data





async def decode_token(token: str):
    auth_data = await get_auth_data()
    try:
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=auth_data['algorithm'])
        return payload
    except JWTError:
        return None