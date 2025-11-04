# API Flow Explanation

## Overview
When you make an API call to your application, it goes through multiple layers before reaching the database and returning data back to the client. This document traces the complete journey.

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENT (Browser or External App)                                    │
│ Makes HTTP Request: GET http://localhost:8080/api/amenities/       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ HTTP Request
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ NGINX (Reverse Proxy) - Port 8080 → 80                             │
│ Container: lbs_nginx (172.28.0.4:80)                               │
│ • Listens for incoming HTTP requests                               │
│ • Forwards all requests to Django/Gunicorn backend                 │
│ • Serves static files (CSS, JS, images)                            │
│ • Adds security headers                                             │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ proxy_pass http://web:8000
                      │ (Internal Docker network)
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ GUNICORN (WSGI App Server) - Port 8000                             │
│ Container: lbs_web (172.28.0.3:8000)                               │
│ • Python application server                                        │
│ • 4 worker processes handling concurrent requests                  │
│ • Receives request and passes to Django                            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ WSGI Application
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ DJANGO Framework (lbs/wsgi.py → lbs/settings.py → lbs/urls.py)   │
│ • Parses the URL path                                              │
│ • Matches URL patterns to views                                    │
│ • Instantiates the appropriate view                                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ URL routing
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ URL ROUTING (lbs/urls.py)                                           │
│ Patterns (matched in order):                                       │
│                                                                     │
│ 1. /admin/ → Django admin interface                                │
│ 2. /api/ → Router.urls (CRUD endpoints)                            │
│    - /api/amenities/           ← Router (AmenityViewSet)          │
│    - /api/areas/               ← Router (AreaViewSet)             │
│    - /api/routes/              ← Router (RouteViewSet)            │
│ 3. /api/amenities/nearest      ← NearestAmenities view            │
│ 4. /api/amenities/within       ← AmenitiesWithinArea view         │
│ 5. /api/amenities/radius       ← AmenitiesWithinRadius view       │
│ 6. /api/routes/intersecting    ← RoutesIntersectingArea view      │
│ 7. /api/routes/radius          ← RoutesWithinRadius view          │
│ 8. / (root)                    → geo.urls (MapView template)      │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ View instantiation
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ VIEW LAYER (geo/views.py)                                           │
│ Class-Based Views (APIView or ViewSet)                             │
│ • Processes request parameters (lat, lng, limit, etc.)            │
│ • Validates input data                                            │
│ • Calls Django ORM to query database                              │
│ • Returns Response with serialized data                           │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ ORM queries
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ DJANGO ORM + GeoDjango (geo/models.py)                              │
│ • Builds SQL queries from Python                                   │
│ • Converts coordinates to Point/LineString objects               │
│ • Performs spatial queries (distance, intersects, within)        │
│ • Translates PostGIS functions                                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ SQL Query
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PostgreSQL + PostGIS (Docker: lbs_db)                               │
│ Container: lbs_db (172.28.0.2:5432)                                 │
│ • Receives SQL query from Django ORM                               │
│ • PostGIS extension processes spatial operations                  │
│ • Returns matching records from database                           │
│ • Uses spatial indexes for performance                             │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ Results
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SERIALIZERS (geo/serializers.py)                                    │
│ • Converts Python objects back to JSON                             │
│ • Uses rest_framework_gis for GeoJSON format                      │
│ • Structures response with features and geometries                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ JSON Response
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RESPONSE (HTTP 200)                                                 │
│ Sent back through: View → Gunicorn → Nginx → Client               │
│                                                                     │
│ Example JSON:                                                       │
│ {                                                                   │
│   "type": "FeatureCollection",                                     │
│   "features": [                                                    │
│     {                                                              │
│       "type": "Feature",                                           │
│       "geometry": {                                                │
│         "type": "Point",                                           │
│         "coordinates": [-6.2477, 53.3434]                          │
│       },                                                            │
│       "properties": {                                              │
│         "id": 1,                                                   │
│         "name": "3fe Grand Canal",                                 │
│         "category": "cafe",                                        │
│         "description": "Coffee shop"                               │
│       }                                                            │
│     }                                                              │
│   ]                                                                │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                      │
                      │ Browser displays on map
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (templates/map.html + Leaflet.js)                         │
│ • Receives GeoJSON                                                 │
│ • Plots markers on interactive map                                 │
│ • User sees results                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Example: `GET /api/amenities/nearest?lat=53.35&lng=-6.26&limit=5`

### Step 1: URL Matching (lbs/urls.py)
```python
path("api/amenities/nearest", NearestAmenities.as_view()),
```
Django matches the incoming URL `/api/amenities/nearest` to this pattern and loads the `NearestAmenities` view.

---

### Step 2: View Processing (geo/views.py)
```python
class NearestAmenities(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # Parse query parameters
        lat = float(request.query_params.get("lat"))           # 53.35
        lng = float(request.query_params.get("lng"))           # -6.26
        limit = int(request.query_params.get("limit", "10"))   # 5
        
        # Create a Point from coordinates (note: lng first!)
        origin = Point(lng, lat, srid=4326)  # POINT(-6.26 53.35)
        
        # Query database
        qs = Amenity.objects.annotate(
            distance=Distance("location", origin)
        ).order_by("distance")[:limit]
        
        # Serialize and return
        serializer = AmenityGeoSerializer(qs, many=True)
        return Response(serializer.data)
```

---

### Step 3: ORM Converts to SQL (geo/models.py + PostGIS)
Django ORM generates this SQL:
```sql
SELECT 
    id, name, category, location, description, source_ref,
    ST_Distance(location, ST_GeomFromText('SRID=4326;POINT(-6.26 53.35)')) AS distance
FROM geo_amenity
ORDER BY distance ASC
LIMIT 5;
```

**Key Points:**
- `ST_Distance()` = PostGIS function calculating distance from Point A to all points
- `ST_GeomFromText()` = Converts coordinates to PostGIS geometry
- Results ordered by distance (nearest first)
- Limited to 5 rows

---

### Step 4: Database Query & Execution
PostgreSQL with PostGIS extension:
1. Receives SQL query
2. Uses spatial index on `location` column (GiST index for fast lookup)
3. Finds 5 nearest amenities from the search point
4. Returns results with calculated distances

**Database Table Structure:**
```sql
CREATE TABLE geo_amenity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(50),
    location GEOMETRY(Point, 4326),  ← Uses SRID 4326 (WGS84)
    description TEXT,
    source_ref VARCHAR(255)
);

CREATE INDEX amenity_location_idx ON geo_amenity USING GIST(location);
```

---

### Step 5: Serialization (geo/serializers.py)
```python
class AmenityGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Amenity
        geo_field = "location"
        fields = ["id", "name", "category", "description", "source_ref"]
```

Converts the 5 database records into GeoJSON format:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-6.2477, 53.3434]
      },
      "properties": {
        "id": 1,
        "name": "3fe Grand Canal",
        "category": "cafe",
        "description": "Coffee shop",
        "source_ref": "sample_001"
      }
    },
    // ... 4 more amenities
  ]
}
```

---

### Step 6: Response Back to Client
1. Gunicorn sends JSON response with `Content-Type: application/json`
2. Nginx forwards response to client
3. Browser receives response
4. Frontend JavaScript (templates/map.html) parses GeoJSON
5. Leaflet.js plots points on the interactive map

---

## API Endpoints Summary

### CRUD Endpoints (Auto-generated by DRF Router)
```
GET    /api/amenities/           → List all amenities
POST   /api/amenities/           → Create new amenity
GET    /api/amenities/{id}/      → Get single amenity
PUT    /api/amenities/{id}/      → Update amenity
DELETE /api/amenities/{id}/      → Delete amenity

GET    /api/areas/               → List all areas
GET    /api/routes/              → List all routes
```

### Spatial Query Endpoints (Custom Views)
```
GET /api/amenities/nearest
    ?lat=53.35&lng=-6.26&limit=5
    → Find 5 nearest amenities to a point

GET /api/amenities/within
    ?area_id=1
    → Find all amenities within a polygon area

GET /api/amenities/radius
    ?lat=53.35&lng=-6.26&km=2
    → Find all amenities within 2km radius

GET /api/routes/intersecting
    ?area_id=1
    → Find all routes that cross/touch an area

GET /api/routes/radius
    ?lat=53.35&lng=-6.26&km=1
    → Find all routes within 1km radius
```

---

## Key Spatial Concepts

### Coordinates Format
- **WGS84 (EPSG:4326)** = Standard GPS coordinates
- **Format**: POINT(longitude latitude)
- **Example**: POINT(-6.26 53.35) = Dublin city center
- **Note**: Longitude (West) comes FIRST, then Latitude (North)

### Spatial Operations
| Operation | SQL Function | Use Case |
|-----------|--------------|----------|
| Distance | `ST_Distance()` | Find nearest points |
| Within | `ST_Within()` | Find points inside polygon |
| Intersects | `ST_Intersects()` | Find crossing paths |
| Buffer | `ST_Buffer()` | Create radius around point |

### PostGIS Indexes
- **GiST Indexes** = Generalized Search Tree for spatial queries
- Applied to: `location` (Point), `path` (LineString), `boundary` (Polygon)
- **Performance**: Allows fast nearest-neighbor and spatial range queries
- Without index: O(n) scan of all records
- With index: O(log n) spatial tree lookup

---

## Request Flow Diagram (Text Version)

```
Browser Request
    ↓
Nginx (Port 8080)
    ↓
Gunicorn Workers (Port 8000)
    ↓
Django URL Router (lbs/urls.py)
    ↓
View (geo/views.py)
    ├─ Parse parameters
    ├─ Validate input
    └─ Call ORM
        ↓
    Django ORM (geo/models.py)
    ├─ Build SQL query
    └─ Translate to PostGIS
        ↓
    PostgreSQL + PostGIS (Port 5432)
    ├─ Use spatial index
    ├─ Execute spatial operation
    └─ Return results
        ↓
    Serializer (geo/serializers.py)
    └─ Convert to GeoJSON
        ↓
    Response (JSON)
        ↓
Nginx (forwards)
    ↓
Browser (renders on map)
```

---

## Adding a New API Endpoint

### Example: Find amenities by category

**1. Add URL pattern (lbs/urls.py):**
```python
path("api/amenities/by-category", AmenitiesByCategory.as_view()),
```

**2. Create view (geo/views.py):**
```python
class AmenitiesByCategory(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        category = request.query_params.get("category")
        if not category:
            raise ValidationError("Query param 'category' is required.")
        
        qs = Amenity.objects.filter(category=category)
        serializer = AmenityGeoSerializer(qs, many=True)
        return Response(serializer.data)
```

**3. Test the endpoint:**
```bash
GET http://localhost:8080/api/amenities/by-category?category=cafe
```

**Request path:**
```
Browser → Nginx → Gunicorn → URL Router → View → ORM → Database → Serializer → JSON → Response
```

---

## Debugging Tips

1. **Check Nginx logs**: `docker compose logs nginx`
2. **Check Django logs**: `docker compose logs web`
3. **Check Database**: Connect via pgAdmin at `localhost:5050` (admin/admin)
4. **Test API directly**: Use curl or Postman to test endpoints
5. **View SQL queries**: Add `?format=json` to any endpoint to see raw JSON response

