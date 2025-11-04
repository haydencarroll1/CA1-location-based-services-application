# Location-Based Services Application — How It Works

A web app that lets you explore amenities (cafes, shops, ATMs, etc) and walking routes in Dublin using an interactive map.

---

## The Three Main Parts

### 1. **The Database** (PostGIS)
Where all the data lives. It stores three main types of things:

- **Amenities** — individual points (lat/lng) like cafes, shops, ATMs
- **Routes** — lines showing walking paths (Grand Canal, Royal Canal)
- **Areas** — shapes showing Dublin committee areas (the big polygons)

All data has a spatial location (coordinates), so the database can answer questions like "what's within 1km of me?" really fast.

**Covered in:** Lecture 5 (spatial models), Lab 2 (data import with GDAL/OGR)

---

### 2. **The Backend API** (Django + DRF)
A REST API that hands out GeoJSON (geographic data in JSON format) when you ask for it.

#### Key Endpoints:

**Load Amenities by Nearest:**
```
GET /api/amenities/nearest/?lat=53.35&lng=-6.26&limit=30
```
Finds the 30 closest amenities to your location.

**Load Amenities by Radius:**
```
GET /api/amenities/radius/?lat=53.35&lng=-6.26&km=1.0
```
Finds all amenities within 1 km of a point.

**Load Routes by Radius:**
```
GET /api/routes/radius/?lat=53.35&lng=-6.26&km=1.0
```
Finds all walking routes within 1 km.

**Load Areas:**
```
GET /api/areas/
```
Gets all Dublin committee area boundaries.

**Load Routes for an Area:**
```
GET /api/routes/intersecting/?area_id=1
```
Finds routes that cross into a specific area.

**How the Backend Works:**
1. Frontend sends a request (e.g., "give me amenities near [lat, lng]")
2. Backend uses GeoDjango to query PostGIS (using spatial lookups like `distance_lte` and `within`)
3. Backend returns GeoJSON (a standard format for geographic data)
4. Frontend receives it and displays it on the map

**Covered in:** Lecture 5 (spatial queries), Lecture 6 (API filtering), Lab 3 (DRF API)

---

### 3. **The Frontend** (Leaflet + JavaScript)
An interactive map in your browser where you can click, search, and filter.

#### What It Does:

**On Page Load:**
1. Asks for your location (geolocation popup)
2. Automatically fetches 30 nearest amenities
3. Shows them as pins on the map

**Two Search Modes:**

**Nearby Mode (default):**
- Click anywhere on the map
- It finds the 30 closest amenities to that spot
- Shows them in a list below the map
- Click a result to zoom to it

**Radius Mode:**
- Click anywhere on the map
- It draws a circle showing your search radius (0.2 – 5 km)
- Finds all amenities + routes inside that circle
- Shows them both on the map and in the list

**Filtering:**
- **Categories** — click buttons (Cafés, Shops, ATMs, etc) to show only those types
- **Search** — type text to filter by name/address/details
- **Areas** — select a Dublin area to see routes that pass through it

**How It Fetches Data:**
```javascript
// Example: fetch amenities within 1km
fetch('/api/amenities/radius/?lat=53.35&lng=-6.26&km=1.0')
  .then(response => response.json())
  .then(data => {
    // data is GeoJSON with amenities
    L.geoJSON(data).addTo(map);  // Leaflet renders it
  });
```

**Covered in:** Lecture 4 (Leaflet basics), Lab 4 (Django + Leaflet integration), Lab 5 (proximity search)

---

## How Data Gets Into the System

### Step 1: Import Amenities (Lab 2 — GDAL/OGR)

Amenities come from OpenStreetMap via an API:

```bash
python manage.py import_osm_amenities --purge --bbox 53.30 -6.35 53.37 -6.20 --limit 100
```

This command:
1. Hits the Overpass API (OpenStreetMap's query service)
2. Asks for cafes, shops, ATMs, etc in a Dublin box
3. Gets GeoJSON back
4. Saves each point to the database with its lat/lng

**Code location:** `geo/management/commands/import_osm_amenities.py`

### Step 2: Import Routes

Routes are stored as GeoJSON files locally (Grand Canal, Royal Canal):

```bash
python manage.py import_routes
```

Reads from:
- `geo/data/routes_grand_canal.geojson`
- `geo/data/routes_royal_canal.geojson`

Each route is a **LineString** (a sequence of points forming a line).

**Code location:** `geo/management/commands/import_routes.py`

### Step 3: Import Areas

Areas are Dublin committee boundaries (also GeoJSON):

```bash
python manage.py import_dcc_areas
```

Each area is a **Polygon** (a shape with a boundary).

**Code location:** `geo/management/commands/import_dcc_areas.py`

**Covered in:** Lab 2 (data engineering with GDAL)

---

## Key Spatial Queries (How the Backend Answers Geographic Questions)

### "What's the nearest N amenities?"

```python
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

origin = Point(lng, lat, srid=4326)
amenities = Amenity.objects.annotate(
    distance=Distance('location', origin)
).order_by('distance')[:30]
```

**What it does:**
1. Creates a point from your coords
2. Calculates distance from that point to every amenity
3. Sorts by distance (closest first)
4. Returns top 30

**Covered in:** Lecture 5 (Distance queries)

### "What's within 1km?"

```python
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point

origin = Point(lng, lat, srid=4326)
amenities = Amenity.objects.filter(
    location__distance_lte=(origin, D(km=1.0))
)
```

**What it does:**
1. Creates a point from your coords
2. Finds all amenities where distance ≤ 1 km
3. Returns them all (no limit)

**Covered in:** Lecture 5 (spatial lookups)

### "What amenities are in this area?"

```python
amenities = Amenity.objects.filter(
    location__within=area.boundary
)
```

**What it does:**
1. Takes a polygon (area boundary)
2. Finds all amenity points inside it
3. Returns them

**Covered in:** Lecture 5 (`within` lookup)

### "What routes cross this area?"

```python
routes = Route.objects.filter(
    path__intersects=area.boundary
)
```

**What it does:**
1. Takes a polygon (area boundary)
2. Finds all route lines that touch or cross it
3. Returns them

**Covered in:** Lecture 5 (`intersects` lookup)

---

## File Structure & Key Code Files

```
geo/
├── models.py              # Amenity, Area, Route models (with spatial fields)
├── views.py               # API endpoints (NearestAmenities, AmenitiesWithinRadius, etc)
├── serializers.py         # Convert models → GeoJSON
├── management/commands/   # Import scripts
│   ├── import_osm_amenities.py
│   ├── import_routes.py
│   └── import_dcc_areas.py
└── data/                  # GeoJSON data files
    ├── routes_grand_canal.geojson
    ├── routes_royal_canal.geojson
    └── ...

templates/
└── map.html               # Frontend (Leaflet map + JavaScript)

lbs/
├── settings.py            # Django config (includes GeoDjango + DRF)
├── urls.py                # Routes to API endpoints
└── wsgi.py / asgi.py      # Server entry points
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────┐
│                    YOUR BROWSER                      │
│  ┌────────────────────────────────────────────────┐  │
│  │   Leaflet Map (map.html)                       │  │
│  │  • Shows pins, routes, area boundaries         │  │
│  │  • Listen for clicks, search input, category   │  │
│  │    clicks                                      │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────┘
                   │ HTTP Requests
                   ↓ (fetch /api/amenities/nearest, etc)
┌──────────────────────────────────────────────────────┐
│              DJANGO BACKEND (views.py)               │
│  ┌────────────────────────────────────────────────┐  │
│  │ NearestAmenities view                          │  │
│  │ • Reads lat/lng/limit from URL params          │  │
│  │ • Queries DB using Distance()                  │  │
│  │ • Returns GeoJSON                              │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ AmenitiesWithinRadius view                     │  │
│  │ • Reads lat/lng/km from URL params             │  │
│  │ • Queries DB using distance_lte lookup         │  │
│  │ • Returns GeoJSON                              │  │
│  └────────────────────────────────────────────────┘  │
│  etc...                                              │
└──────────────────┬───────────────────────────────────┘
                   │ SQL Queries
                   ↓ (using PostGIS spatial functions)
┌──────────────────────────────────────────────────────┐
│         POSTGIS DATABASE (PostgreSQL)                │
│  ┌────────────────────────────────────────────────┐  │
│  │ amenity table (points)                         │  │
│  │ • id, name, category, location (Point)         │  │
│  │ • indexed for fast spatial lookups              │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ route table (linestrings)                      │  │
│  │ • id, name, path (LineString)                  │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ area table (polygons)                          │  │
│  │ • id, name, boundary (Polygon)                 │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | What It Does | Lecture |
|-------|-----------|-------------|---------|
| **Frontend** | Leaflet.js | Interactive map, pins, popups, layer controls | Lecture 4 |
| **Frontend Logic** | JavaScript | Fetch API, event handlers, UI state | Lab 4 |
| **API** | Django REST Framework | Serves GeoJSON endpoints | Lecture 3 |
| **Spatial Queries** | GeoDjango ORM | Nearest, within-radius, area-based queries | Lecture 5 |
| **Database** | PostGIS/PostgreSQL | Stores geographic data, runs spatial lookups | Lecture 5, Lab 2 |
| **Data Import** | GDAL/OGR | Reads GeoJSON/Shapefiles, loads into DB | Lab 2 |

---

## What Gets Covered from Lectures (and what doesn't)

### ✅ **Covered in This App**

- **Lecture 4:** Leaflet basics (map setup, markers, popups, layer controls)
- **Lecture 5:** Spatial queries (Distance, within, intersects, annotate)
- **Lecture 6:** API filtering + search (though we do it mostly client-side)
- **Lab 2:** Data import with GDAL/OGR (import_osm_amenities, etc)
- **Lab 3:** DRF API structure (viewsets, serializers, GeoJSON response)
- **Lab 4:** Django + Leaflet integration (fetching API in HTML page)
- **Lab 5:** Proximity search (nearest, radius endpoints)
- **Lab 6:** Multi-layer filtering (category chips, search input, area selection)

### ❌ **Not Covered (or Minimal)**

- **Lecture 3:** We don't use server-rendered HTML templates (it's a REST API + SPA)
- **Lecture 6:** Advanced versioning strategies (we use a single API version)
- **Lab 6:** Formal statistics endpoints (we have results count, but not aggregate stats)
- Advanced authentication / permissions (we allow all requests)

---

## Data Sources & Loading

All sample data is stored in two locations:

### **Fixtures** (`geo/fixtures/`)
- `dcc_admin_areas.json` – Dublin City Council 5 committee areas (boundaries)
- `amenities_sample.json` – Curated sample of 25 amenities (points)

Loaded via Django's `loaddata` command:
```bash
python manage.py loaddata geo/fixtures/dcc_admin_areas.json
python manage.py loaddata geo/fixtures/amenities_sample.json
```

### **GeoJSON Data Files** (`geo/data/`)
- `routes_grand_canal.geojson` – Grand Canal walking route (LineString)
- `routes_royal_canal.geojson` – Royal Canal walking route (LineString)

Imported via custom management command:
```bash
python manage.py import_routes
```

**How Data is Sourced:**
- **Amenities:** Curated from Dublin OpenStreetMap data (cafes, shops, ATMs, parks, etc.)
- **Areas:** Dublin City Council 5 Committee Areas (public administrative boundaries, EPSG:2157 → EPSG:4326)
- **Routes:** Public walking routes digitized from Dublin canal maps

**In Docker:** Data is automatically loaded during startup (see docker-compose.yml command).

---

## Running the App

### Local (with Docker database):

```bash
# Terminal 1: Start database
docker compose up db

# Terminal 2: Start Django
source .venv/bin/activate
python manage.py runserver

# Open browser to http://localhost:8000
```

### Docker (full stack):

```bash
DOCKER_BUILDKIT=0 docker compose up --build
# Open browser to http://localhost:8080
```

---

## Example User Journey

1. **Page loads**
   - Browser requests geolocation
   - Backend fetches 30 nearest amenities
   - Map shows pins

2. **User clicks "Radius Mode"**
   - UI changes to show radius slider (0.2–5 km)

3. **User clicks on map at some point**
   - Frontend captures click (lat/lng)
   - Sends: `GET /api/amenities/radius/?lat=53.35&lng=-6.26&km=1.0`
   - Also sends: `GET /api/routes/radius/?lat=53.35&lng=-6.26&km=1.0`
   - Backend returns GeoJSON for amenities + routes
   - Frontend displays them on map + in list

4. **User clicks "Cafés" category chip**
   - Frontend re-filters the already-loaded amenities (client-side)
   - List updates to show only cafes

5. **User types "Starbucks" in search**
   - Frontend filters amenities by name (client-side)
   - List shows only matching results

6. **User clicks an amenity in the list**
   - Map zooms to that pin
   - Popup opens

---

## Summary

This app teaches you an **industry-standard workflow**: data lives in a spatial database, you expose it via a REST API, and a Leaflet frontend consumes it dynamically. Instead of server-rendered pages or desktop GIS, you get a **decoupled, scalable, testable** architecture that mirrors real production apps.

The heavy lifting (proximity, area filters, intersections) happens in **PostGIS** (via GeoDjango ORM), not in JavaScript. The frontend is just a smart consumer of your API.

