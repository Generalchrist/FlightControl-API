import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from FlightControl_API.services.commandService import CommandService


class CommandConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.send_data_task = asyncio.create_task(
            CommandService.send_commands_data(self))

    async def disconnect(self, close_code):
        if hasattr(self, 'send_data_task'):
            self.send_data_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "command_response":
            await CommandService.handle_command_response(self, data["data"])
