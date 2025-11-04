# Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                           │
│                    (Leaflet.js + Bootstrap)                      │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                    HTTP/HTTPS (Port 8080)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx Reverse Proxy                         │
│              (nginx:latest, Port 8080→80)                        │
│                                                                   │
│  - Routes requests to Django/Gunicorn                            │
│  - Serves static files (CSS, JS, images)                         │
│  - Handles SSL termination (if configured)                       │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                    HTTP (Port 8000)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Django Application + Gunicorn                      │
│                      (Port 8000)                                  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Django REST Framework                      │    │
│  │                                                          │    │
│  │  Endpoints:                                             │    │
│  │  - /api/amenities/          [GET]                       │    │
│  │  - /api/amenities/nearby/   [GET with filters]          │    │
│  │  - /api/routes/             [GET]                       │    │
│  │  - /api/admin-areas/        [GET]                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Django ORM + GeoDjango                        │    │
│  │                                                          │    │
│  │  - Models: Amenity, Route, AdminArea                    │    │
│  │  - Spatial Field Types: PointField, LineStringField     │    │
│  │  - Query Methods: Distance, Within, Intersects          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │        Django REST Serializers (GeoJSON)                │    │
│  │                                                          │    │
│  │  - GeoFeatureModelSerializer                            │    │
│  │  - Converts models to GeoJSON features                  │    │
│  │  - Includes geometry and properties                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                   TCP (Port 5432)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL 16 + PostGIS 3.5                         │
│                      (Port 5432)                                  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            Spatial Database                             │    │
│  │                                                          │    │
│  │  Tables:                                                │    │
│  │  - geo_amenity (point geometries)                        │    │
│  │  - geo_route (linestring geometries)                     │    │
│  │  - geo_adminarea (polygon geometries)                    │    │
│  │                                                          │    │
│  │  Indexes:                                               │    │
│  │  - GiST spatial indexes on geometry columns             │    │
│  │  - B-tree indexes on frequently queried columns         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  PostGIS Functions Used:                                         │
│  - ST_Distance: Calculate distance between geometries            │
│  - ST_DWithin: Find geometries within distance                   │
│  - ST_Intersects: Find overlapping geometries                    │
│  - ST_Contains: Spatial containment queries                      │
│                                                                   │
│  Data Volume:                                                    │
│  - ~25 amenity records                                           │
│  - 2 route records (canal routes)                                │
│  - 5 administrative area records                                 │
│                                                                   │
│  Persistence:                                                    │
│  - db_data Docker volume (survives container restarts)           │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow Example: Search for Nearby Amenities

```
1. User clicks "Search Nearby" on map
         │
         ▼
2. JavaScript sends GET request
   /api/amenities/nearby/?lat=53.35&lon=-6.26&radius=1000
         │
         ▼
3. Nginx routes to Django (Port 8000)
         │
         ▼
4. Django View: NearbyAmenitiesView
   - Receives lat, lon, radius parameters
   - Creates Point(lon, lat) geometry
         │
         ▼
5. GeoDjango ORM Query
   Amenity.objects.filter(
       location__distance_lte=(point, Distance(m=radius))
   )
         │
         ▼
6. Django ORM translates to SQL with PostGIS
   SELECT * FROM geo_amenity 
   WHERE ST_DWithin(location, ST_Point(-6.26, 53.35), 1000)
         │
         ▼
7. PostgreSQL executes query
   - Uses GiST spatial index on location column
   - Returns matching amenity records
         │
         ▼
8. Django Serializer: GeoFeatureModelSerializer
   Converts results to GeoJSON FeatureCollection
         │
         ▼
9. Response sent to browser as JSON
         │
         ▼
10. Leaflet.js adds features to map as markers/popups
```

## Data Flow

### At Application Startup

```
Docker Compose Up
      │
      ├─→ PostgreSQL container starts
      │   └─→ Creates database 'dae_db'
      │   └─→ PostGIS extension installed
      │   └─→ Spatial tables created via migrations
      │
      ├─→ Django/Gunicorn container starts
      │   ├─→ Runs migrations: python manage.py migrate
      │   ├─→ Loads fixtures: python manage.py loaddata
      │   │   └─→ Inserts pre-defined amenities and areas
      │   ├─→ Import routes: python manage.py import_routes
      │   │   └─→ Reads GeoJSON files
      │   │   └─→ Parses geometries
      │   │   └─→ Creates Route objects in database
      │   └─→ Starts Gunicorn server (4 worker processes)
      │
      └─→ Nginx container starts
          └─→ Configured to proxy to Django
```

### User Interaction Flow

```
User visits http://localhost:8080
         │
         ▼
Nginx serves index.html (static file)
         │
         ▼
Browser downloads:
  - base.html (layout template)
  - map.html (page template)
  - app.css (styling)
  - Leaflet.js library
  - Leaflet CSS
         │
         ▼
JavaScript initializes:
  1. Creates Leaflet map
  2. Sets center to Dublin (53.3498° N, 6.2603° W)
  3. Adds OpenStreetMap tiles
         │
         ▼
Fetch GeoJSON from API:
  GET /api/amenities/
         │
         ▼
Leaflet displays features:
  - Amenities as clickable markers
  - Routes as polylines
  - Admin areas as polygon overlays
         │
         ▼
User interacts:
  - Pan/zoom map
  - Click amenity → popup with details
  - Search form → query API with filters
```

## Component Interactions

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Frontend** | User interface and map display | HTML/CSS/JavaScript + Leaflet.js |
| **Reverse Proxy** | Routes traffic, serves static files | Nginx |
| **Application Server** | Processes API requests | Django + Gunicorn |
| **ORM Layer** | Database abstraction | Django ORM + GeoDjango |
| **Spatial Database** | Stores and queries geographic data | PostgreSQL + PostGIS |

### Dependency Graph

```
Browser
   ↓
Leaflet.js (map library)
   ↓ (AJAX requests)
Nginx (reverse proxy)
   ↓ (HTTP routing)
Gunicorn (4 worker processes)
   ↓
Django REST Framework
   ↓ (ORM queries)
GeoDjango
   ↓ (SQL with PostGIS)
PostgreSQL + PostGIS
```

## Deployment Options

### Option 1: Full Docker Stack (Production-like)
```
All services in Docker containers
Nginx → Django → PostgreSQL
Volumes for data persistence
Environment-based configuration
```

### Option 2: Hybrid (Development)
```
Docker: PostgreSQL only
Local: Django development server
Better for debugging and rapid iteration
```

## Performance Considerations

### Database Optimization
- **Spatial Indexes**: GiST indexes on all geometry columns for O(log n) spatial queries
- **Connection Pooling**: Configured in production deployments
- **Query Optimization**: GeoDjango uses efficient spatial predicates

### Caching Opportunities
- Amenity list changes infrequently (candidate for HTTP caching)
- Static tiles cached by browser and CDN
- Database query results could be cached with Redis (future enhancement)

### Scalability
- **Horizontal**: Add more Gunicorn workers or separate web servers
- **Vertical**: Increase Docker resource limits
- **Database**: PostGIS handles large geographic datasets efficiently
