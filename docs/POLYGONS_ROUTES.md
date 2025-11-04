# Polygons and Routes Explanation

## Overview

Your project uses **three types of geometric data**:

1. **Points** (Amenities) - Single locations with latitude/longitude
2. **LineStrings** (Routes) - Connected paths/lines across the map
3. **Polygons** (Areas) - Closed boundaries defining regions

This document explains how routes and polygons work, with visual examples.

---

## Geometry Types in Your Project

### 1. Points (Amenities) ✓
```
┌─────────────────────────────────────┐
│                                     │
│  ● Cafe         ● ATM              │
│     ● Park                ● Shop   │
│       ● Gym                        │
│                                     │
└─────────────────────────────────────┘

Each dot is a POINT geometry at coordinates (longitude, latitude)
Example: POINT(-6.2477 53.3434) = Specific cafe location
```

**In your database:**
```python
class Amenity(models.Model):
    location = models.PointField(srid=4326)  # ← Single point
```

---

### 2. LineStrings (Routes) 
```
┌─────────────────────────────────────┐
│                                     │
│  ●─────●─────●                    │
│   Grand Canal Route                │
│        ●─────●─────●               │
│        Royal Canal Route           │
│                                     │
└─────────────────────────────────────┘

Each dot is a vertex, connected in sequence
Example: LINESTRING(lon1 lat1, lon2 lat2, lon3 lat3, ...)
```

**In your database:**
```python
class Route(models.Model):
    path = models.LineStringField(srid=4326)  # ← Sequence of connected points
```

---

### 3. Polygons (Areas)
```
┌──────────────────────────────────────┐
│                                      │
│  ┌─────────────────────────┐        │
│  │  NORTH WEST (area)      │        │
│  │ (closed polygon)        │        │
│  └─────────────────────────┘        │
│  ┌───────────────┐   ┌────────────┐ │
│  │NORTH CENTRAL  │   │ SOUTH WEST │ │
│  └───────────────┘   └────────────┘ │
│                                      │
└──────────────────────────────────────┘

A polygon is a closed boundary with multiple vertices
The first and last coordinates must be identical to close the shape
```

**In your database:**
```python
class Area(models.Model):
    boundary = models.PolygonField(srid=4326)  # ← Closed shape (polygon)
```

---

## Data Format: How Geometry is Stored

### SRID=4326 Prefix
All geometries include `SRID=4326;` which means:
- **SRID** = Spatial Reference ID
- **4326** = WGS84 (World Geodetic System 1984)
- Standard GPS coordinates system

### Format: (Longitude, Latitude)
**IMPORTANT:** Coordinates are `(longitude first, latitude second)`
- Longitude = East-West position (−180° to +180°)
- Latitude = North-South position (−90° to +90°)
- Dublin center: `POINT(-6.26 53.35)` = 6.26°W, 53.35°N

---

## Routes: LineStrings in Detail

### What is a Route?

A **Route** is a path connecting multiple locations in sequence. Your project has:
1. **Grand Canal Route** - Path through Dublin's Grand Canal
2. **Royal Canal Route** - Path through Dublin's Royal Canal

### Fixture Format (How Routes are Stored)

```json
{
  "model": "geo.route",
  "pk": 1,
  "fields": {
    "name": "Grand Canal Route",
    "path": "SRID=4326;LINESTRING(
      -6.70790 53.25986,    ← Starting point (longitude, latitude)
      -6.70800 53.25990,    ← Second point
      -6.70808 53.25994,    ← Third point
      ... (many more points) ...
      -6.76000 53.27100     ← Ending point
    )"
  }
}
```

### How Routes Work

**Your current fixture has 61 vertices** that create a continuous line:

```
Start (−6.70790, 53.25986)
  ↓
  ├─ Vertex 1 (−6.70800, 53.25990)
  ├─ Vertex 2 (−6.70808, 53.25994)
  ├─ Vertex 3 (−6.70875, 53.26015)
  ├─ ... (57 more vertices)
  ├─ Vertex 60 (−6.75900, 53.27080)
  ↓
End (−6.76000, 53.27100)

All 61 points connected = One continuous line (the route path)
```

### Geographic Interpretation

The Grand Canal Route represents the actual path of Dublin's Grand Canal:
- **Starts** at southern part of Dublin (−6.70790, 53.25986)
- **Ends** at northern area (−6.76000, 53.27100)
- **Follows** the real canal's winding path
- **61 vertices** = Level of detail in the path

### API Endpoint: Get All Routes

```bash
GET /api/routes/
```

Response:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-6.70790, 53.25986],
          [-6.70800, 53.25990],
          [-6.70808, 53.25994],
          ...
          [-6.76000, 53.27100]
        ]
      },
      "properties": {
        "id": 1,
        "name": "Grand Canal Route"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-6.36340, 53.36880],
          [-6.36330, 53.36870],
          ...
        ]
      },
      "properties": {
        "id": 2,
        "name": "Royal Canal Route"
      }
    }
  ]
}
```

### Spatial Query: Routes Within Radius

```bash
GET /api/routes/radius?lat=53.35&lng=-6.26&km=1
```

**How it works:**
1. Creates a center point: `POINT(-6.26 53.35)`
2. Creates a 1km buffer (radius) around that point
3. Finds all routes that intersect with that buffer
4. Returns matching routes as GeoJSON

**SQL generated by PostGIS:**
```sql
SELECT * FROM geo_route
WHERE ST_DWithin(
  path,
  ST_GeomFromText('SRID=4326;POINT(-6.26 53.35)'),
  1000  -- 1000 meters = 1 km
)
```

---

## Polygons: Detailed Explanation

### What is a Polygon (Area)?

Your project has **5 Dublin administrative areas**:
1. **NORTH WEST**
2. **NORTH CENTRAL**
3. **SOUTH WEST**
4. **SOUTH EAST**
5. **CENTRAL**

Each area is a polygon defining a region's boundaries.

### Polygon Structure

A polygon is defined by:
- A closed loop of vertices (first point = last point)
- Multiple connected line segments forming a closed shape
- Optional holes (not used in your project)

```
Example simple polygon (a square):
POLYGON((
  -6.30 53.40,   ← Start (top-left)
  -6.20 53.40,   ← (top-right)
  -6.20 53.30,   ← (bottom-right)
  -6.30 53.30,   ← (bottom-left)
  -6.30 53.40    ← Back to start (MUST be identical)
))

Your polygons are complex with 800+ vertices each!
```

### Your "NORTH WEST" Polygon

From `dcc_admin_areas.json`, pk=21:

```
POLYGON((-6.30628... 53.40144..., -6.30628... 53.40144..., ...))
```

**Decoded:**
- **2,100+ vertices** defining the boundary
- **Closed loop** from Dublin's northwest corner
- **Represents** the North West Dublin City administrative area
- **Used for** spatial queries like "find all cafes in North West"

### Visualizing the Polygon

```
Real Dublin Map:           Your GIS Database:
┌──────────────────┐      POLYGON((
│ ╭─ North West ─╮│         -6.30 53.40,
│ │ ╭─────────────┤│         -6.25 53.41,
│ │ │  North      ││         -6.24 53.40,
│ │ │  Central    ││         ... (2100+ more points)
│ │ ├─ Central ──┐││         -6.30 53.40  ← closes loop
│ │ │╭─────────│┤││      ))
│ │ ││  South  ││││
│ │ │├─ East ──┤┤││
│ │ │╰─────────╯║││
│ ╰─────────────╯│
│                │
└──────────────────┘
```

### API Endpoint: Get All Areas

```bash
GET /api/areas/
```

Response:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-6.30628, 53.40144],
            [-6.30628, 53.40144],
            [-6.30637, 53.40147],
            ... (2100+ vertices)
            [-6.30628, 53.40144]  ← Closes the loop
          ]
        ]
      },
      "properties": {
        "id": 21,
        "name": "NORTH WEST"
      }
    }
  ]
}
```

---

## Spatial Queries: Polygon Operations

### 1. Points Within Polygon

```bash
GET /api/amenities/within?area_id=21
```

**What it does:**
- Finds the North West area polygon
- Finds all amenities (points) inside this polygon
- Returns them as GeoJSON

**SQL:**
```sql
SELECT * FROM geo_amenity
WHERE ST_Within(
  location,
  (SELECT boundary FROM geo_area WHERE id = 21)
)
```

**Visualization:**
```
┌────────────────────────┐
│  NORTH WEST AREA       │
│  (polygon boundary)    │
│                        │
│   ●café   ● park      │ ← These are returned
│                        │
│   ●gym    ● atm       │ ← These are returned
│                        │
└────────────────────────┘
     ● cafe outside       ← NOT returned
```

### 2. Routes Crossing Polygon

```bash
GET /api/routes/intersecting?area_id=21
```

**What it does:**
- Finds all routes (linestrings) that cross/touch the polygon boundary
- Routes can pass through, partially cross, or touch the edge

**SQL:**
```sql
SELECT * FROM geo_route
WHERE ST_Intersects(
  path,
  (SELECT boundary FROM geo_area WHERE id = 21)
)
```

**Visualization:**
```
Before query:
Route 1 ─────────────────────────
         (might cross area)

Route 2 ────
         (might not intersect)

After query:
┌──────────────────────┐
│  NORTH WEST AREA     │
│                      │
│ Route 1 passes through ← RETURNED
│ ──────────────────   │
│                      │
└──────────────────────┘

Route 2 (separate) ─ ← NOT RETURNED
```

---

## Spatial Indexes: Why Polygons & Routes Are Fast

Your database has spatial indexes on:
- `amenity.location` (PointField) → GiST index
- `route.path` (LineStringField) → GiST index
- `area.boundary` (PolygonField) → GiST index

**Without index:** Database checks every single record (slow)
**With GiST index:** Database uses spatial tree to find candidates (fast)

```
GiST Tree for Areas:
            [All Polygons]
           /      |      \
      [NW]     [NC]     [SC]
       / \       /\       /\
   [parts]...[parts]...[parts]...

Query: "Find areas at (-6.26, 53.35)"
Result: GiST tree narrows down to 1-2 candidates instantly
```

---

## Model Structure in Code

### Area Model
```python
class Area(models.Model):
    name = models.CharField(max_length=100)
    boundary = models.PolygonField(srid=4326)  # Polygon geometry
```

### Route Model
```python
class Route(models.Model):
    name = models.CharField(max_length=100)
    path = models.LineStringField(srid=4326)   # LineString geometry
```

### Serializers (Convert to GeoJSON)
```python
class AreaGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Area
        geo_field = "boundary"   # ← Use boundary as geometry
        fields = ("id", "name")

class RouteGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Route
        geo_field = "path"       # ← Use path as geometry
        fields = ("id", "name")
```

---

## Frontend: How Leaflet Displays Them

### Displaying on Map

```javascript
// Frontend receives GeoJSON from /api/routes/
const response = await fetch('/api/routes/');
const routes = await response.json();

// Leaflet adds to map
L.geoJSON(routes, {
  style: {
    color: 'blue',
    weight: 3,
    opacity: 0.7
  }
}).addTo(map);
```

### Visual Result on Map

```
Map Display:
┌────────────────────────────────────┐
│ Dublin City                        │
│                                    │
│  🔵═══ Grand Canal Route          │
│   (Blue line with 3px width)      │
│                                    │
│  🔵 ══ Royal Canal Route          │
│   (Blue line with 3px width)      │
│                                    │
│  [Colored regions for areas]      │
│  [Red dots for amenities]         │
│                                    │
└────────────────────────────────────┘
```

---

## Creating New Routes/Polygons

### Adding a New Route

1. **Create GeoJSON LineString** (e.g., from mapping tool)
2. **Convert to fixture format** in `geo/fixtures/new_route.json`:
```json
[
  {
    "model": "geo.route",
    "pk": 3,
    "fields": {
      "name": "New Canal Route",
      "path": "SRID=4326;LINESTRING(-6.25 53.30, -6.26 53.31, -6.27 53.32)"
    }
  }
]
```

3. **Load fixture**:
```bash
python manage.py loaddata geo/fixtures/new_route.json
```

### Adding a New Area

1. **Create GeoJSON Polygon** (e.g., from mapping tool)
2. **Convert to fixture format**:
```json
[
  {
    "model": "geo.area",
    "pk": 26,
    "fields": {
      "name": "My New Area",
      "boundary": "SRID=4326;POLYGON((-6.25 53.30, -6.26 53.30, -6.26 53.31, -6.25 53.31, -6.25 53.30))"
    }
  }
]
```

3. **Load fixture**:
```bash
python manage.py loaddata geo/fixtures/new_area.json
```

---

## Common Spatial Operations

| Operation | Function | Use Case |
|-----------|----------|----------|
| **Distance** | `ST_Distance()` | How far is route from amenity? |
| **Within** | `ST_Within()` | Is amenity inside area? |
| **Intersects** | `ST_Intersects()` | Does route cross area? |
| **Contains** | `ST_Contains()` | Does polygon contain point? |
| **Buffer** | `ST_Buffer()` | Create radius around point |
| **Length** | `ST_Length()` | How long is the route (meters)? |

---

## Summary

- **Points (Amenities)**: Single locations, stored as `POINT(lon lat)`
- **LineStrings (Routes)**: Connected paths, stored as `LINESTRING(lon1 lat1, lon2 lat2, ...)`
- **Polygons (Areas)**: Closed regions, stored as `POLYGON((lon1 lat1, ..., lon1 lat1))`
- **All use SRID=4326** (WGS84 GPS coordinates)
- **All have GiST spatial indexes** for fast queries
- **All serialize to GeoJSON** for frontend mapping display
- **Spatial queries** find relationships between these geometries

Your project leverages **PostGIS** (PostgreSQL spatial extension) to perform these spatial operations efficiently at the database level!

