import json
from typing import Dict

from fastapi import APIRouter, HTTPException
from faststream import Depends
from faststream.rabbit.fastapi import RabbitRouter
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, Response

from src.shared.dependencies.service_deps import auth_service
from src.shared.dependencies.user_deps import current_user


router = APIRouter(prefix="/auth", tags=['Auth'])


@router.get("/")
async def login_page(request: Request, user: current_user):
    if user:
        return RedirectResponse("http://127.0.0.1:8000/")
    context = {
               "title": "Вход",
               }
    return JSONResponse(context)


@router.get('/login')
async def login(request: Request, service: auth_service):
    redirect_uri = "http://127.0.0.1:8000/auth/github/callback"
    return await service.oauth.github.authorize_redirect(request, redirect_uri)


@router.get('/github/callback')
async def callback(request: Request, service: auth_service):
    try:
        token = await service.oauth.github.authorize_access_token(request)
        user = await service.oauth.github.get("user", token=token)
        email = await service.oauth.github.get("user/emails", token=token)
        user_data = user.json()
        email_data = email.json()

        res = await service.register_user(user_data, email_data)
        if not res:
            raise HTTPException(status_code=400, detail="User registration failed")

        user_id = res[0]
        tokens = await service.get_token(user_id)

        response = JSONResponse({
            "success": True,
            "username": res[1],
            "avatar_url": res[2],
            "email": res[3],
            "message": "Login successful"
        })
        response.set_cookie(
            "access_token",
            tokens["access_token"],
            # max_age=1800,
            secure=False,
            httponly=True,
            samesite="lax"
        )
        response.set_cookie(
            "refresh_token",
            tokens["refresh_token"],
            max_age=43200 * 60,
            secure=False,
            httponly=True,
            samesite="lax"
        )

        return response
    except Exception as e:
        raise HTTPException(
            detail={"success": False, "error": str(e)},
            status_code=400
        )

@router.get('/refresh')
async def refresh(request: Request, service: auth_service, response: Response):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=401, detail='Not Authorized')
    # response = Response()
    token = await service.refresh(refresh_token)
    if token:
        response.set_cookie('access_token',
                            token['token'],
                            # max_age=1800,
                            secure=False,
                            httponly=True,
                            samesite="lax"
                            )
        return {'access_token': token['token']}
    else:
        response.delete_cookie('refresh_token')
        raise HTTPException(status_code=403, detail="Invalid refresh")

@router.get("/logout")
async def logout(request: Request, service: auth_service):
    refresh_token = request.cookies.get("refresh_token")
    await service.logout(refresh_token)
    response = RedirectResponse("/auth")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
