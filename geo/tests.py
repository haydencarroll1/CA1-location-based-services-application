from django.contrib.gis.geos import Point, Polygon, LineString
from rest_framework.test import APIClient
from django.test import TestCase

from .models import Amenity, Area, Route


class SpatialQueryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.area = Area.objects.create(
            name="Test Area",
            boundary=Polygon((
                (-6.28, 53.33),
                (-6.20, 53.33),
                (-6.20, 53.37),
                (-6.28, 53.37),
                (-6.28, 53.33),
            ), srid=4326),
        )
        self.route = Route.objects.create(
            name="River Walk",
            path=LineString(
                (-6.27, 53.35),
                (-6.21, 53.35),
                srid=4326,
            ),
        )
        self.cafe = Amenity.objects.create(
            name="Brew Lab",
            category="cafe",
            location=Point(-6.26, 53.35, srid=4326),
            description="Coffee spot",
        )
        self.gym = Amenity.objects.create(
            name="Lift Hub",
            category="gym",
            location=Point(-6.25, 53.34, srid=4326),
            description="Fitness center",
        )
        self.outside = Amenity.objects.create(
            name="Far Cafe",
            category="cafe",
            location=Point(-6.24, 53.38, srid=4326),
            description="Outside area",
        )

    def test_nearest_amenities_limit_validation(self):
        response = self.client.get("/api/amenities/nearest", {"lat": 53.35, "lng": -6.26, "limit": "abc"})
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        if isinstance(payload, list):
            text = " ".join(str(item) for item in payload)
        else:
            detail = payload.get("detail", "")
            text = str(detail)
        self.assertIn("limit", text.lower())

    def test_nearest_amenities_returns_sorted_results(self):
        response = self.client.get("/api/amenities/nearest", {"lat": 53.35, "lng": -6.26, "limit": 2})
        self.assertEqual(response.status_code, 200)
        names = [f["properties"]["name"] for f in response.json()["features"]]
        self.assertEqual(names[0], "Brew Lab")

    def test_amenities_within_area(self):
        response = self.client.get("/api/amenities/within", {"area_id": self.area.pk})
        self.assertEqual(response.status_code, 200)
        names = [f["properties"]["name"] for f in response.json()["features"]]
        self.assertIn("Brew Lab", names)
        self.assertIn("Lift Hub", names)

    def test_routes_intersecting_area(self):
        response = self.client.get("/api/routes/intersecting", {"area_id": self.area.pk})
        self.assertEqual(response.status_code, 200)
        names = [f["properties"]["name"] for f in response.json()["features"]]
        self.assertIn("River Walk", names)

    def test_amenities_within_radius(self):
        response = self.client.get(
            "/api/amenities/radius",
            {"lat": 53.35, "lng": -6.26, "km": 0.5},
        )
        self.assertEqual(response.status_code, 200)
        names = [f["properties"]["name"] for f in response.json()["features"]]
        self.assertIn("Brew Lab", names)

    def test_radius_validation_requires_positive_km(self):
        response = self.client.get(
            "/api/amenities/radius",
            {"lat": 53.35, "lng": -6.26, "km": -1},
        )
        self.assertEqual(response.status_code, 400)

    def test_nearest_respects_area_filter(self):
        response = self.client.get(
            "/api/amenities/nearest",
            {"lat": 53.35, "lng": -6.26, "limit": 5, "area_id": self.area.pk},
        )
        self.assertEqual(response.status_code, 200)
        names = {f["properties"]["name"] for f in response.json()["features"]}
        self.assertIn("Brew Lab", names)
        self.assertNotIn("Far Cafe", names)

    def test_radius_respects_area_filter(self):
        response = self.client.get(
            "/api/amenities/radius",
            {"lat": 53.35, "lng": -6.26, "km": 5, "area_id": self.area.pk},
        )
        self.assertEqual(response.status_code, 200)
        names = {f["properties"]["name"] for f in response.json()["features"]}
        self.assertIn("Brew Lab", names)
        self.assertNotIn("Far Cafe", names)
