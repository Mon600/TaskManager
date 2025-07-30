from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response, JSONResponse

from src.project.management_service.routers.link import accept_invite
from src.shared.dependencies.service_deps import auth_service
from src.shared.dependencies.user_deps import current_user

router = APIRouter(prefix="/auth", tags=['Auth'])


@router.get("/")
async def login_page(request: Request, user: current_user):
    if user:
        return RedirectResponse("http://127.0.0.1:8002/")
    context = {
               "title": "Вход",
               }
    return JSONResponse(context)


@router.get('/login')
async def login(request: Request, service: auth_service):
    redirect_uri = "http://127.0.0.1:8002/auth/github/callback"
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

        # Устанавливаем куки
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
            max_age=1800,
            secure=False,  # Для локальной разработки
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
        # Редирект на frontend
        response.headers["Location"] = "http://localhost:3000/auth/success"
        response.status_code = 302  # Found
        return response
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=400
        )


@router.get("/success")
async def success_login(
        request: Request):
    context = {
        "username": request.session.get('username'),
        "avatar_url": request.session.get("avatar_url"),
        "email": request.session.get("email"),
        "title": "Вы успешно вошли"
    }
    try:
        request.session.pop('username')
        request.session.pop('avatar_url')
        request.session.pop('email')
    except KeyError:
        print("Keys not found.")
    return JSONResponse(context)


@router.get('/refresh')
async def refresh(request: Request, refresh_token: str, service: auth_service):
    access_token = await service.refresh(refresh_token)
    response = JSONResponse({'ok': True, 'token': access_token}, status_code=200)
    return response


@router.get("/logout")
async def logout(request: Request, service: auth_service):
    refresh_token = request.cookies.get("refresh_token")
    await service.logout(refresh_token)
    response = RedirectResponse("/auth")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
