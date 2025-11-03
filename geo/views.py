from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError

from .models import Amenity, Area, Route
from .serializers import AmenityGeoSerializer, AreaGeoSerializer, RouteGeoSerializer
from .filters import AmenityFilter

# ---- CRUD ----
class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenityGeoSerializer
    filterset_class = AmenityFilter
    search_fields = ["name", "description", "category"]
    ordering_fields = ["name", "category", "id"]
    permission_classes = [IsAuthenticatedOrReadOnly]

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaGeoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteGeoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ---- Spatial queries ----
class NearestAmenities(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
        except (TypeError, ValueError):
            raise ValidationError("Query params 'lat' and 'lng' are required floats.")
        limit_param = request.query_params.get("limit", "10")
        try:
            limit = int(limit_param)
        except (TypeError, ValueError):
            raise ValidationError("Query param 'limit' must be a positive integer.")
        if limit <= 0:
            raise ValidationError("Query param 'limit' must be greater than zero.")
        limit = min(limit, 100)
        origin = Point(lng, lat, srid=4326)
        qs = Amenity.objects.annotate(distance=Distance("location", origin)).order_by("distance")[:limit]
        serializer = AmenityGeoSerializer(qs, many=True)
        return Response(serializer.data)

class AmenitiesWithinArea(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        area_id = request.query_params.get("area_id")
        if not area_id:
            raise ValidationError("Query param 'area_id' is required.")
        try:
            area = Area.objects.get(pk=area_id)
        except Area.DoesNotExist:
            raise ValidationError("Area not found.")
        qs = Amenity.objects.filter(location__within=area.boundary)
        serializer = AmenityGeoSerializer(qs, many=True)
        return Response(serializer.data)

class RoutesIntersectingArea(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        area_id = request.query_params.get("area_id")
        if not area_id:
            raise ValidationError("Query param 'area_id' is required.")
        try:
            area = Area.objects.get(pk=area_id)
        except Area.DoesNotExist:
            raise ValidationError("Area not found.")
        qs = Route.objects.filter(path__intersects=area.boundary)
        serializer = RouteGeoSerializer(qs, many=True)
        return Response(serializer.data)

class AmenitiesWithinRadius(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
            km = float(request.query_params.get("km", "1.0"))
        except (TypeError, ValueError):
            raise ValidationError("Params 'lat','lng','km' are required floats.")
        origin = Point(lng, lat, srid=4326)
        qs = Amenity.objects.filter(location__distance_lte=(origin, D(km=km)))
        serializer = AmenityGeoSerializer(qs, many=True)
        return Response(serializer.data)
