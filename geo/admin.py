from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Amenity, Area, Route

@admin.register(Amenity)
class AmenityAdmin(OSMGeoAdmin):
    list_display = ("id","name","category")
    search_fields = ("name","category")
    default_lon = -6.2603
    default_lat = 53.3498
    default_zoom = 12

@admin.register(Area)
class AreaAdmin(OSMGeoAdmin):
    list_display = ("id","name")

@admin.register(Route)
class RouteAdmin(OSMGeoAdmin):
    list_display = ("id","name")
