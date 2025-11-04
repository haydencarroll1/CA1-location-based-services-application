# Database Schema Documentation

## Overview

This document describes the database schema for the Location Based Services application. The database uses PostgreSQL with the PostGIS extension for spatial data support.

## Database: `dae_db`

PostgreSQL 16 with PostGIS 3.5 extension enabled.

## Tables

### 1. `geo_amenity`

Stores points of interest (amenities) in Dublin.

```sql
CREATE TABLE geo_amenity (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    amenity_type VARCHAR(100),
    location GEOMETRY(Point, 4326) NOT NULL,
    source_ref VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE AUTO_NOW_ADD,
    updated_at TIMESTAMP WITH TIME ZONE AUTO_NOW
);
```

#### Fields

| Field | Type | Description | Example |
|-------|------|-----------|---------|
| `id` | BIGSERIAL | Unique identifier | 1, 2, 3... |
| `name` | VARCHAR(255) | Name of the amenity | "Marlay Park" |
| `description` | TEXT | Detailed description | "Public park with walking trails..." |
| `amenity_type` | VARCHAR(100) | Category/type | "park", "library", "parking" |
| `location` | GEOMETRY(Point, 4326) | Geographic point coordinates (WGS84) | POINT(-6.26 53.35) |
| `source_ref` | VARCHAR(255) | Reference to source (e.g., OSM ID) | "way:123456" |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation timestamp | 2025-11-04 10:30:00+00:00 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update timestamp | 2025-11-04 10:30:00+00:00 |

#### Indexes

```sql
-- Spatial index for location-based queries
CREATE INDEX geo_amenity_location_gist ON geo_amenity USING GIST (location);

-- Standard indexes for common queries
CREATE INDEX geo_amenity_amenity_type_idx ON geo_amenity (amenity_type);
CREATE INDEX geo_amenity_name_idx ON geo_amenity (name);
```

#### Example Query

```sql
-- Find all parks within 1km of Dublin city center (53.3498, -6.2603)
SELECT name, amenity_type, description 
FROM geo_amenity 
WHERE ST_DWithin(
    location, 
    ST_Point(-6.2603, 53.3498, 4326)::geography, 
    1000
) 
AND amenity_type = 'park';
```

---

### 2. `geo_route`

Stores geographic routes (e.g., canal routes in Dublin).

```sql
CREATE TABLE geo_route (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    route_type VARCHAR(100),
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    length_meters FLOAT,
    created_at TIMESTAMP WITH TIME ZONE AUTO_NOW_ADD,
    updated_at TIMESTAMP WITH TIME ZONE AUTO_NOW
);
```

#### Fields

| Field | Type | Description | Example |
|-------|------|-----------|---------|
| `id` | BIGSERIAL | Unique identifier | 1, 2... |
| `name` | VARCHAR(255) | Route name | "Grand Canal Route" |
| `description` | TEXT | Route details | "Historic canal running through Dublin..." |
| `route_type` | VARCHAR(100) | Type of route | "canal", "river", "greenway" |
| `geometry` | GEOMETRY(LineString, 4326) | Path coordinates (WGS84) | LINESTRING(-6.3 53.35, -6.25 53.35, ...) |
| `length_meters` | FLOAT | Total route length | 12500.5 |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation timestamp | 2025-11-04 10:30:00+00:00 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update timestamp | 2025-11-04 10:30:00+00:00 |

#### Indexes

```sql
-- Spatial index for geometry queries
CREATE INDEX geo_route_geometry_gist ON geo_route USING GIST (geometry);

-- Standard indexes
CREATE INDEX geo_route_route_type_idx ON geo_route (route_type);
CREATE INDEX geo_route_name_idx ON geo_route (name);
```

#### Example Query

```sql
-- Find all routes that pass through a specific area
SELECT name, length_meters, route_type 
FROM geo_route 
WHERE ST_Intersects(
    geometry, 
    ST_Buffer(ST_Point(-6.26, 53.35, 4326)::geography, 2000)
);
```

---

### 3. `geo_adminarea`

Stores administrative boundaries (e.g., Dublin DCC committee areas).

```sql
CREATE TABLE geo_adminarea (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    area_code VARCHAR(50),
    description TEXT,
    geometry GEOMETRY(Polygon, 4326) NOT NULL,
    area_sq_meters FLOAT,
    created_at TIMESTAMP WITH TIME ZONE AUTO_NOW_ADD,
    updated_at TIMESTAMP WITH TIME ZONE AUTO_NOW
);
```

#### Fields

| Field | Type | Description | Example |
|-------|------|-----------|---------|
| `id` | BIGSERIAL | Unique identifier | 1, 2, 3... |
| `name` | VARCHAR(255) | Area name | "Ballymun-Finglas" |
| `area_code` | VARCHAR(50) | Official area code | "A01", "A02", etc. |
| `description` | TEXT | Area description | "Committee area in north Dublin..." |
| `geometry` | GEOMETRY(Polygon, 4326) | Boundary polygon (WGS84) | POLYGON((-6.3 53.4, -6.2 53.4, ...)) |
| `area_sq_meters` | FLOAT | Total area in square meters | 5500000 |
| `created_at` | TIMESTAMP WITH TIME ZONE | Record creation timestamp | 2025-11-04 10:30:00+00:00 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Last update timestamp | 2025-11-04 10:30:00+00:00 |

#### Indexes

```sql
-- Spatial index for containment and intersection queries
CREATE INDEX geo_adminarea_geometry_gist ON geo_adminarea USING GIST (geometry);

-- Standard indexes
CREATE INDEX geo_adminarea_area_code_idx ON geo_adminarea (area_code);
CREATE INDEX geo_adminarea_name_idx ON geo_adminarea (name);
```

#### Example Query

```sql
-- Find all amenities within a specific administrative area
SELECT a.name, a.amenity_type 
FROM geo_amenity a 
WHERE ST_Contains(
    (SELECT geometry FROM geo_adminarea WHERE name = 'Ballymun-Finglas'),
    a.location
);
```

---

## Django Models (ORM Representation)

### Amenity Model
```python
class Amenity(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amenity_type = models.CharField(max_length=100)
    location = PointField(srid=4326)
    source_ref = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    geo_objects = GeoManager()
    
    class Meta:
        indexes = [
            GiSTIndex(fields=['location']),
        ]
```

### Route Model
```python
class Route(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    route_type = models.CharField(max_length=100)
    geometry = LineStringField(srid=4326)
    length_meters = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    geo_objects = GeoManager()
    
    class Meta:
        indexes = [
            GiSTIndex(fields=['geometry']),
        ]
```

### AdminArea Model
```python
class AdminArea(models.Model):
    name = models.CharField(max_length=255)
    area_code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    geometry = PolygonField(srid=4326)
    area_sq_meters = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    geo_objects = GeoManager()
    
    class Meta:
        indexes = [
            GiSTIndex(fields=['geometry']),
        ]
```

## Spatial Reference System (SRS)

All geometry data uses **EPSG:4326** (WGS84), the standard geographic coordinate system:
- **SRID**: 4326
- **Coordinates**: Longitude (X), Latitude (Y)
- **Units**: Degrees
- **Precision**: ~1.1cm at equator

### Coordinate Convention
- **Longitude**: -6.26 (West) to -6.27 (for Dublin)
- **Latitude**: 53.35 (North)

**Example**: Dublin city center = POINT(-6.2603, 53.3498)

## Spatial Indexes

All tables use **GiST (Generalized Search Tree)** indexes on geometry columns for efficient spatial queries:

```sql
CREATE INDEX geo_amenity_location_gist ON geo_amenity USING GIST (location);
CREATE INDEX geo_route_geometry_gist ON geo_route USING GIST (geometry);
CREATE INDEX geo_adminarea_geometry_gist ON geo_adminarea USING GIST (geometry);
```

### Performance

- **Query Time**: O(log n) for spatial queries
- **Index Size**: ~30% of table size
- **Insert/Update**: Slightly slower due to index maintenance
- **Benefit**: 10-100x faster for spatial queries on large datasets

## PostGIS Functions Used

### Distance Functions
- `ST_Distance(geom1, geom2)` - Calculate distance between geometries
- `ST_DWithin(geom1, geom2, distance)` - Check if geometries are within distance
- `ST_Buffer(geom, distance)` - Create buffer around geometry

### Relationship Functions
- `ST_Intersects(geom1, geom2)` - Check if geometries intersect
- `ST_Contains(geom1, geom2)` - Check if one geometry contains another
- `ST_Touches(geom1, geom2)` - Check if geometries touch but don't overlap

### Utility Functions
- `ST_Point(lon, lat, srid)` - Create point geometry
- `ST_Length(geom)` - Calculate line length
- `ST_Area(geom)` - Calculate polygon area
- `ST_AsGeoJSON(geom)` - Convert to GeoJSON format

## Data Loading

### Fixture Data

Sample data is provided in JSON format:

**`geo/fixtures/dcc_admin_areas.json`** - 5 Dublin committee areas

**`geo/fixtures/amenities_sample.json`** - 25 sample amenities

### Import Command

**`geo/management/commands/import_routes.py`** - Loads canal routes from GeoJSON files:
- `geo/data/routes_grand_canal.geojson`
- `geo/data/routes_royal_canal.geojson`

## Backup & Recovery

### Database Backup

```bash
# Backup database to SQL dump
docker exec lbs_db pg_dump -U postgres dae_db > backup.sql

# Backup with GeoJSON export
docker exec lbs_db psql -U postgres dae_db -c \
  "SELECT row_to_json(t) FROM geo_amenity t" > amenities_backup.geojson
```

### Database Restore

```bash
# Restore from SQL dump
docker exec -i lbs_db psql -U postgres dae_db < backup.sql

# Full Docker reset (WARNING: deletes all data)
docker compose down -v
```

## Future Enhancements

1. **Spatial Triggers**: Auto-calculate `length_meters` for routes
2. **Topology Layer**: Validate spatial relationships between features
3. **Partitioning**: Partition large tables by geographic quadrants
4. **Full-Text Search**: Add PostgreSQL full-text search indexes
5. **History Tracking**: Implement temporal data with `tsrange` type
