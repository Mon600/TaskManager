
from fastapi import APIRouter, Form
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from src.project.email_service.celery_worker.tasks import send_mail_task
from src.shared.dependencies.service_deps import user_service, auth_service
from src.shared.dependencies.user_deps import current_user


router = APIRouter(prefix='/email', tags=['Email'])


@router.post("/send")
async def send_mail(request: Request,
                    user: current_user,
                    auth: auth_service,
                    service: user_service,
                    email: str =  Form(...)):
    if user is None:
        return RedirectResponse('/auth')
    code = await service.generate_code(email, user.id)
    subject = "Подтверждение email"
    body = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <div class="header">
            <h2>Подтверждение email</h2>
        </div>
        <p>Здравствуйте!</p>
        <p>Пожалуйста, подтвердите ваш email:</p>
        <a href="http://127.0.0.1:8000/email/confirm/{code}" class="button">Подтвердить</a>
        <p>Ссылка: http://127.0.0.1:8000/email/confirm/{code}</p>
    </body>
    </html>
    """
    celery_task = BackgroundTask(send_mail_task.delay, email, subject, body)
    return JSONResponse({"ok": True}, background=celery_task)


@router.get("/confirm/{code}")
async def email_confirm(request: Request,
                        code: str,
                        user_service: user_service):

    res = await user_service.confirm_email(code)
    context = {"request": request,
               "success": res,
               "title": "Подтверждение email"}

    return JSONResponse(context)

