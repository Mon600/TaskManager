import asyncio




class SocketIOHandlers:
    def __init__(self, sio):
        self.sio = sio
        asyncio.run(self.register_handlers())

    async def register_handlers(self):
        @self.sio.on('enter_room')
        async def request_hello(sid, data):
            roomname = f'project_{data}'
            print(f'user {sid} joined to {roomname}')
            await self.sio.enter_room(sid, room=roomname)