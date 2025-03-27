import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from FlightControl_API.services.planeService import PlaneService
from FlightControl_API.services.commandService import CommandService


class PlaneConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        self.send_data_task = asyncio.create_task(
            PlaneService.send_plane_data(self))
        self.send_data_task = asyncio.create_task(
            CommandService.send_commands_data(self))

    async def disconnect(self, close_code):
        if hasattr(self, 'send_data_task'):
            self.send_data_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "send_command":
            await CommandService.handle_send_command(self,data["data"])
