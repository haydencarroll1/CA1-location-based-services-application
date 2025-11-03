from django.contrib.gis.db import models

class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    boundary = models.PolygonField(srid=4326)

    def __str__(self):
        return self.name


class Route(models.Model):
    name = models.CharField(max_length=100, unique=True)
    path = models.LineStringField(srid=4326)

    def __str__(self):
        return self.name


class Amenity(models.Model):
    CATEGORIES = [
        ("cafe", "Cafe"),
        ("gym", "Gym"),
        ("atm", "ATM"),
        ("park", "Park"),
        ("shop", "Shop"),
    ]
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    location = models.PointField(srid=4326)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.name} ({self.category})"
