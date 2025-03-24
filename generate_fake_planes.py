import os
import django
from faker import Faker
import random
from django.contrib.gis.geos import Point

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlightControl_API.settings')
django.setup()
from FlightControl_API.models import Plane

fake = Faker()

def generate_planes(n):
    planes = []
    for _ in range(n):
        plane_id = fake.uuid4()  # Generate a unique UUID for each plane
        pilot_id = fake.random_int(min=1000, max=9999)  # Random pilot ID
        # Generate random latitude and longitude for location
        latitude = random.uniform(-90, 90)  # Latitude range [-90, 90]
        longitude = random.uniform(-180, 180)  # Longitude range [-180, 180]
        
        # Create a Point with valid latitude and longitude
        location = Point(longitude, latitude)

        plane = Plane(plane_id=plane_id, pilot_id=pilot_id, location=location)
        planes.append(plane)

    Plane.objects.bulk_create(planes)  # Bulk insert for better performance

if __name__ == "__main__":
    generate_planes(10000)
