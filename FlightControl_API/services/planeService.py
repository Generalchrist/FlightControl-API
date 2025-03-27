import json
import asyncio
from FlightControl_API.models import Plane
from asgiref.sync import sync_to_async


class PlaneService():
    async def send_plane_data(self):
        while True:
            planes = await sync_to_async(list)(
                Plane.objects.only("plane_id", "pilot_id", "location")
            )

            plane_data = []
            for plane in planes:
                plane.location.x += 0.025

                plane_data.append({
                    "plane_id": plane.plane_id,
                    "pilot_id": plane.pilot_id,
                    "location": {
                        "latitude": plane.location.y,
                        "longitude": plane.location.x,
                    },
                })

            await sync_to_async(Plane.objects.bulk_update)(
                planes, ["location"]
            )

            await self.send(text_data=json.dumps({"planes": plane_data}))

            await asyncio.sleep(0.1)
