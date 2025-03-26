import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from FlightControl_API.models import Command, Plane
from asgiref.sync import sync_to_async
from django.contrib.gis.geos import Point
from django.db.models import F


class PlaneConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the connection is for commands or planes
        if self.scope['path'] == '/ws/commands/':
            self.type = 'commands'
        elif self.scope['path'] == '/ws/planes/':
            self.type = 'planes'
        else:
            await self.close()
            return

        # Accept the WebSocket connection
        await self.accept()

        # Based on connection type, start corresponding task
        if self.type == 'commands':
            self.send_data_task = asyncio.create_task(
                self.send_commands_data())
        elif self.type == 'planes':
            self.send_data_task = asyncio.create_task(self.send_plane_data())

    async def disconnect(self, close_code):
        if hasattr(self, 'send_data_task'):
            self.send_data_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "send_command":
            await self.handle_send_command(data["data"])

        elif data.get("type") == "command_response":
            await self.handle_command_response(data["data"])


# TODO: HELPERS


    async def send_plane_data(self):
        while True:
            # Fetch only required fields to improve query speed
            planes = await sync_to_async(list)(
                Plane.objects.only("plane_id", "pilot_id", "location")
            )

            plane_data = []
            for plane in planes:
                plane.location.x += 0.025

                # Append for WebSocket update
                plane_data.append({
                    "plane_id": plane.plane_id,
                    "pilot_id": plane.pilot_id,
                    "location": {
                        "latitude": plane.location.y,
                        "longitude": plane.location.x,
                    },
                })

            # Bulk update all planes in a single query
            await sync_to_async(Plane.objects.bulk_update)(
                planes, ["location"]
            )

            # Send updated plane data to frontend
            await self.send(text_data=json.dumps({"planes": plane_data}))

            # Sleep before next update
            await asyncio.sleep(0.1)

    async def send_commands_data(self):
        while True:
            # Fetch commands and send to connected clients
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

            # Send the commands data
            await self.send(text_data=json.dumps({"commands": command_data}))
            await asyncio.sleep(1)

    async def handle_send_command(self, data):
        """
        Handle incoming command data, save to database, and notify frontend.
        """
        # Extract information from the command
        plane_id = data.get("plane_id")
        pilot_id = data.get("pilot_id")
        drop_off_location = data.get("drop_off_location")
        message = data.get("message")

        # Convert drop_off_location to a Point object
        latitude = drop_off_location.get("latitude")
        longitude = drop_off_location.get("longitude")
        # Correct order for Point (longitude, latitude)
        point = Point(longitude, latitude)

        # Create a new Command object
        command = await sync_to_async(Command.objects.create)(
            plane_id=plane_id,
            pilot_id=pilot_id,
            drop_off_location=point,
            message=message,
        )

        # Broadcast the new command to all connected clients
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

        # Send the command to the frontend
        await self.send(text_data=json.dumps({
            "type": "new_command",
            "data": command_data
        }))

    async def handle_command_response(self, data):
        """
        Handle the response of the pilot to the command (accepted/rejected).
        Update the command status and notify all clients.
        """
        command_id = data.get("command_id")
        status = data.get("status")

        # Ensure status is valid
        if status not in ["accepted", "rejected"]:
            return

        # Get the command and update the status
        command = await sync_to_async(Command.objects.get)(id=command_id)
        command.status = status
        await sync_to_async(command.save)()

        # Prepare the updated command data
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

        # Notify all connected clients with the updated command status
        await self.send(text_data=json.dumps({
            "type": "updated_command",
            "data": command_data
        }))
