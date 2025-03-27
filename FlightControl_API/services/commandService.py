import json
import asyncio
from FlightControl_API.models import Command
from asgiref.sync import sync_to_async
from django.contrib.gis.geos import Point


class CommandService():
    async def send_commands_data(self):
        while True:
            commands = await sync_to_async(list)(
                Command.objects.only(
                    "id", "plane_id", "pilot_id", "message", "drop_off_location", "status", "created_at")
            )
            command_data = [
                {
                    "id": command.id,
                    "plane_id": command.plane_id,
                    "pilot_id": command.pilot_id,
                    "message": command.message,
                    "location": {
                        "latitude": command.drop_off_location.y,
                        "longitude": command.drop_off_location.x,
                    },
                    "status": command.status,
                    "created_at": command.created_at.isoformat(),
                }
                for command in commands
            ]

            await self.send(text_data=json.dumps({"commands": command_data}))
            await asyncio.sleep(11)

    async def handle_send_command(self, data):
        plane_id = data.get("plane_id")
        pilot_id = data.get("pilot_id")
        drop_off_location = data.get("drop_off_location")
        message = data.get("message")

        latitude = drop_off_location.get("latitude")
        longitude = drop_off_location.get("longitude")

        point = Point(longitude, latitude)

        command = await sync_to_async(Command.objects.create)(
            plane_id=plane_id,
            pilot_id=pilot_id,
            drop_off_location=point,
            message=message,
        )

        command_data = {
            "plane_id": command.plane_id,
            "pilot_id": command.pilot_id,
            "message": command.message,
            "drop_off_location": {
                "latitude": command.drop_off_location.y,  # y is latitude
                "longitude": command.drop_off_location.x,  # x is longitude
            },
            "status": command.status,
            "created_at": command.created_at.isoformat(),
        }

        await self.send(text_data=json.dumps({
            "type": "new_command",
            "data": command_data
        }))

    async def handle_command_response(self, data):
        command_id = data.get("command_id")
        status = data.get("status")

        if status not in ["accepted", "rejected"]:
            return

        command = await sync_to_async(Command.objects.get)(id=command_id)
        command.status = status
        await sync_to_async(command.save)()

        command_data = {
            "plane_id": command.plane_id,
            "pilot_id": command.pilot_id,
            "message": command.message,
            "drop_off_location": {
                "latitude": command.drop_off_location.y,
                "longitude": command.drop_off_location.x,
            },
            "status": command.status,
            "created_at": command.created_at.isoformat(),
        }

        await self.send(text_data=json.dumps({
            "type": "updated_command",
            "data": command_data
        }))
