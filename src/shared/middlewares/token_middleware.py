import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx


class RefreshTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        timestamp = datetime.datetime.now().timestamp()
        last_time = request.session.get('last_time_timestamp', 0)
        if (timestamp - last_time) > 600:
            refresh_token = request.cookies.get('refresh_token')
            if not refresh_token:
                return response

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "http://127.0.0.1:8002/auth/refresh",
                        params={"refresh_token": refresh_token}
                    )
                if resp.status_code == 200:
                    access_token = resp.json()['token']['token']
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        max_age=30 * 60,
                        secure=True,
                        httponly=True,
                        samesite="strict"
                    )
                    request.session['last_time_timestamp'] = timestamp
            except Exception:
                print("Authorization service unavailable")
                pass

        return response