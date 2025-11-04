# User Guide - Location Based Services Application

## Overview

This is a location-based services web application that displays geographic data on an interactive map. It allows users to explore amenities and routes in Dublin, Ireland using spatial queries and visualization.

## Getting Started

### Prerequisites
- Docker and Docker Compose (or Python 3.12 + PostgreSQL 16 with PostGIS)
- A web browser with JavaScript enabled

### Quick Start with Docker

1. **Start the application:**
   ```bash
   docker compose up --build
   ```

2. **Access the application:**
   - Open http://localhost:8080 in your browser
   - The map interface will load with Dublin's amenities and routes

3. **Stop the application:**
   ```bash
   docker compose down
   ```

### Alternative: Local Development Setup

If you prefer running Django locally with Docker database:

```bash
# Start only the database
docker compose up db -d

# Install Python dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load sample data
python manage.py loaddata geo/fixtures/dcc_admin_areas.json
python manage.py loaddata geo/fixtures/amenities_sample.json
python manage.py import_routes

# Start Django development server
python manage.py runserver

# Access at http://localhost:8000
```

## Features

### Interactive Map
- **Pan & Zoom**: Use mouse to navigate the map
- **Search by Location**: Find amenities near specific coordinates
- **View Routes**: Visualize Dublin's Grand Canal and Royal Canal routes
- **Explore Admin Areas**: See Dublin's DCC committee areas

### API Endpoints

#### Amenities
- `GET /api/amenities/` - List all amenities
- `GET /api/amenities/<id>/` - Get specific amenity details
- `GET /api/amenities/nearby/?lat=53.35&lon=-6.26&radius=1000` - Find nearby amenities (radius in meters)

#### Routes
- `GET /api/routes/` - List all routes
- `GET /api/routes/<id>/` - Get route details

#### Admin Areas
- `GET /api/admin-areas/` - List all administrative areas

### Spatial Queries

The application supports spatial queries including:
- **Distance-based search**: Find amenities within a specified radius
- **Intersection queries**: Identify amenities in specific administrative areas
- **Boundary checks**: Determine if locations fall within certain regions

## Database

### Connection Details (Docker)

- **Host**: localhost
- **Port**: 5432
- **Database**: dae_db
- **Username**: postgres
- **Password**: postgres

### Viewing Data

#### Using pgAdmin (Web Interface)
1. The application includes pgAdmin at http://localhost:5050
2. Login credentials: admin@example.com / admin
3. Add a new server:
   - Hostname: `db`
   - Port: 5432
   - Username: postgres
   - Password: postgres

#### Using psql (Command Line)
```bash
psql -h localhost -U postgres -d dae_db
```

## Data

### Sample Data Included
- **Amenities**: 25 sample amenities across Dublin (parks, libraries, services)
- **Routes**: Grand Canal and Royal Canal routes with full geometries
- **Admin Areas**: Dublin's DCC committee areas for area-based queries

### Loading Additional Data

To load custom GeoJSON data:

```bash
python manage.py import_routes
```

## Troubleshooting

### Connection Refused Error
- **Problem**: Cannot connect to database
- **Solution**: Ensure Docker containers are running with `docker compose ps`
- **For local setup**: Check that PostgreSQL is running on the correct port

### Map Not Loading
- **Problem**: Blank map or JavaScript errors
- **Solution**: 
  - Check browser console (F12) for errors
  - Ensure API endpoints are responding: `curl http://localhost:8080/api/amenities/`
  - Verify web container is healthy: `docker compose ps`

### Slow Queries
- **Problem**: Map takes time to load or queries are slow
- **Solution**: 
  - Spatial indexes are automatically created on PostGIS columns
  - For large datasets, consider adding more database indexes

### Docker Container Exits
- **Problem**: Services crash or exit unexpectedly
- **Solution**: 
  - Check logs: `docker compose logs web` or `docker compose logs db`
  - Ensure sufficient disk space and memory
  - Try rebuilding: `docker compose down -v && docker compose up --build`

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](./ARCHITECTURE.md)

For database schema details, see [SCHEMA.md](./SCHEMA.md)

## Support & Documentation

- **API Documentation**: Available at `/api/` endpoint
- **Django Admin**: Access at http://localhost:8080/admin/ (local setup only)
- **Code Documentation**: See inline comments in `geo/models.py`, `geo/views.py`, and `geo/serializers.py`
