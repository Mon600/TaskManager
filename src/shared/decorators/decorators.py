import datetime
from functools import wraps
from fastapi import HTTPException






def PermissionsChecker(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = kwargs.get('project')
            user = kwargs.get('user')
            project_id = kwargs.get('project_id')

            if not all([service, user, project_id]):
                raise HTTPException(
                    status_code=400,
                    detail="Missing required parameters (service, user or project_id)"
                )

            user_role = await service.is_user_project_member(project_id, user['id'])
            if user_role is None:
                raise HTTPException(status_code=401, detail="No access")
            if user['id'] == user_role['user_id']:
                role = user_role['role_rel']
                is_access = role.get(permission, None)
                if is_access:
                    return await func(*args, **kwargs)
            raise HTTPException(status_code=401, detail="No access")
        return wrapper
    return decorator

