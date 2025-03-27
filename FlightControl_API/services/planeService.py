import json
import asyncio
from django.contrib.gis.db.models.functions import Translate
from asgiref.sync import sync_to_async
from FlightControl_API.models import Plane


class PlaneService():
    async def send_plane_data(self):
        while True:
            await sync_to_async(Plane.objects.update)(
                location=Translate("location", 0.025, 0)
            )

            planes = await sync_to_async(lambda: list(
                Plane.objects.values("plane_id", "pilot_id", "location")
            ))()

            plane_data = [{
                "plane_id": plane["plane_id"],
                "pilot_id": plane["pilot_id"],
                "location": {
                    "latitude": plane["location"].y,
                    "longitude": plane["location"].x,
                } if plane["location"] else None
            } for plane in planes]

            await self.send(text_data=json.dumps({"planes": plane_data}))

            await asyncio.sleep(1)
