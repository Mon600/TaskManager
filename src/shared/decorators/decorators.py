import functools

from fastapi import HTTPException


def is_user(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if user is None:
            raise HTTPException(401, detail='Unauthorized')
        return await func(*args, **kwargs)
    return wrapper