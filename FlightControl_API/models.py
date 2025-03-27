from django.contrib.gis.db import models


class Plane(models.Model):
    pilot_id = models.IntegerField()
    plane_id = models.CharField(max_length=50, unique=True)
    location = models.PointField()

    def __str__(self):
        return f"Plane {self.plane_id} (Pilot ID: {self.pilot_id})"


class Command(models.Model):
    plane_id = models.CharField(max_length=50)
    pilot_id = models.IntegerField()
    message = models.TextField()
    drop_off_location = models.PointField()
    # 'pending', 'accepted', 'rejected'
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Command for Plane {self.plane_id} - Status: {self.status}"
