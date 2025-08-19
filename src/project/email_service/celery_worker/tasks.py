import asyncio
import datetime
import smtplib
import logging
from email.message import EmailMessage

from sqlalchemy import delete

from src.project.email_service.celery_worker.celery_config import celery_app as app
from src.shared.db.models import ProjectLink
from src.shared.config import async_session

logger = logging.getLogger(__name__)
host = app.conf.SMTP_HOST
port = app.conf.SMTP_PORT
user = app.conf.SMTP_USER
password = app.conf.SMTP_PASSWORD


def send_yandex_mail(to: str, subject: str, body: str) -> bool:
    try:
        SMTP_PARAMS = {
            'host': host,
            'port': 465,
            'username': user,
            'password': password,
            'timeout': 20
        }

        msg = EmailMessage()
        msg["From"] = SMTP_PARAMS['username']
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body, subtype='html')

        with smtplib.SMTP_SSL(
                host=SMTP_PARAMS['host'],
                port=SMTP_PARAMS['port'],
                timeout=SMTP_PARAMS['timeout']
        ) as server:
            server.login(SMTP_PARAMS['username'], SMTP_PARAMS['password'])
            server.send_message(msg)

        return True

    except Exception as e:
        logger.warning(f"Ошибка отправки: {e}")
        return False


@app.task(bind=True, max_retries=3)
def send_mail_task(self, to: str, subject: str, body: str):
    try:
        if not send_yandex_mail(to, subject, body):
            self.retry(countdown=60)
    except Exception as e:
        self.retry(exc=e, countdown=120)


@app.task(bind=True, max_retries=3)
def clear_links(self):
    try:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(clear_links_async())
        asyncio.run(clear_links_async())
    except Exception as e:
        logger.warning(f'{e}')
        self.retry(countdown=5)

async def clear_links_async():
    current_date = datetime.datetime.now()
    async with async_session() as session:
        try:
            stmt = delete(ProjectLink).where(ProjectLink.end_at <= current_date)
            await session.execute(stmt)
            await session.commit()
            print("Задача выполнена")
        except Exception as exc:
            logger.warning(f"Error: {exc}")
            raise exc

