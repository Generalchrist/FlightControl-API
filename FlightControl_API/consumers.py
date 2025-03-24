import json
import asyncio
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from FlightControl_API.models import Command, Plane
from asgiref.sync import sync_to_async
from django.contrib.gis.geos import Point

class PlaneConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.send_data_task = asyncio.create_task(self.send_plane_data())

    async def disconnect(self, close_code):
        if hasattr(self, 'send_data_task'):
            self.send_data_task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Handle send_command type
        if data.get("type") == "send_command":
            await self.handle_send_command(data["data"])


# TODO: HELPERS

    async def send_plane_data(self):
        while True:
            # Fetch only required fields to improve query speed
            planes = await sync_to_async(list)(
                Plane.objects.only("plane_id", "pilot_id", "location")
            )

            plane_data = []
            for plane in planes:
                plane.location.x += 0.05

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
            await asyncio.sleep(0.01)

    async def handle_send_command(self, data):
        """
        Handle incoming command data, save to database, and notify frontend.
        """
        # Extract information from the command
        print(data)
        plane_id = data.get("plane_id")
        pilot_id = data.get("pilot_id")
        drop_off_location = data.get("drop_off_location")
        message = data.get("message")

        # Convert drop_off_location to a Point object
        latitude = drop_off_location.get("latitude")
        longitude = drop_off_location.get("longitude")
        point = Point(longitude, latitude)  # Correct order for Point (longitude, latitude)

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