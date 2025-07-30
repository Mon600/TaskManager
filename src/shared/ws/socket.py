import socketio
from socketio import AsyncRedisManager

from src.shared.ws.ws import SocketIOHandlers

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', logger=True, client_manager=AsyncRedisManager("redis://localhost:6379/0"))
SocketIOHandlers(sio)