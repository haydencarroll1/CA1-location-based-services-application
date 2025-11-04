# Dublin Amenities Explorer

Find nearby amenities and walking routes in Dublin on an interactive Leaflet map. Click to search, draw a radius, or filter by area—all via a GeoDjango + PostGIS spatial API.

## Features

- **Nearest Search** – Find 30 closest amenities to any map point
- **Radius Search** – Draw a circle (0.2–5 km) to find amenities + routes
- **Area Filtering** – See amenities and routes within Dublin administrative areas
- **Category & Text Filters** – Refine results by type (cafés, shops, ATMs, parks) or name
- **REST API + GeoJSON** – Django REST Framework serves spatial queries; Leaflet visualizes

## Quick Start

```bash
# 1. Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Database
createdb dae_db
psql -d dae_db -c "CREATE EXTENSION postgis;"

# 3. Configure & migrate
cp .env.example .env  # Update DB credentials if needed
python manage.py migrate

# 4. Load sample data
python manage.py loaddata geo/fixtures/dcc_admin_areas.json
python manage.py loaddata geo/fixtures/amenities_sample.json
python manage.py import_routes

# 5. Run
python manage.py runserver
# Visit http://127.0.0.1:8000/
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/amenities/nearest?lat=X&lng=Y&limit=30` | 30 nearest amenities |
| `GET /api/amenities/radius?lat=X&lng=Y&km=2` | Amenities within 2km |
| `GET /api/routes/radius?lat=X&lng=Y&km=2` | Routes within 2km |
| `GET /api/areas/` | All Dublin areas |
| `GET /api/amenities/` | All amenities (paginated) |

## How It Works (30 seconds)

1. Leaflet map captures a click or draws a radius
2. Frontend calls `/api/amenities/radius?lat=...&lng=...&km=...`
3. GeoDjango queries PostGIS using spatial indexes (GiST)
4. API returns GeoJSON FeatureCollection
5. Leaflet renders markers, lines, and popups

## Project Structure

```
geo/
├── models.py              # Amenity, Area, Route (spatial models)
├── views.py               # API endpoints (DRF viewsets)
├── serializers.py         # GeoJSON serialization
└── management/commands/
    └── import_routes.py   # Load route data

templates/map.html         # Interactive Leaflet UI
lbs/settings.py            # Django + GeoDjango config
deploy/nginx.conf          # Nginx reverse proxy (Docker)
```

## Docker Deployment (Bonus)

```bash
DOCKER_BUILDKIT=0 docker compose up --build
# Visit http://localhost:8080/
```

**Includes:**
- Multi-stage Dockerfile (optimized for arm64 Mac)
- Custom Docker network (172.28.0.0/16)
- Nginx reverse proxy with security headers
- Automatic data load + migrations on startup

See `DOCKER_IMPROVEMENTS.md` for full setup.

## Assessment Alignment

| Requirement | Status | Details |
|-------------|--------|---------|
| **PostGIS Spatial DB** | ✅ | Points, lines, polygons with GiST indexes |
| **≥3 Spatial Queries** | ✅ | nearest, radius, within, intersects |
| **MVC Architecture** | ✅ | Django models/views + DRF |
| **Responsive Leaflet UI** | ✅ | Bootstrap 5, works mobile/tablet/desktop |
| **Local Deployment** | ✅ | Manual or Docker (bonus +5 marks) |

## Documentation

- **FUNCTIONALITY_GUIDE.md** – Deep dive on architecture, code examples, data flow
- **DOCKER_IMPROVEMENTS.md** – Complete Docker setup, security hardening, optimization notes
- **geo/fixtures/** – Sample data (amenities, areas)
- **geo/data/** – GeoJSON reference files (routes, boundaries)

## Known Limitations

- Local deployment only (no cloud hosting)
- No user authentication (public API, suitable for assignment scope)
