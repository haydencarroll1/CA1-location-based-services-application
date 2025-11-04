"""
Django management command to import route GeoJSON files into the database.

This command reads GeoJSON files containing route geometries (LineString or MultiLineString)
and creates or updates Route objects in the database. It handles coordinate transformation
to WGS84 (EPSG:4326) and supports bulk operations with optional reset functionality.

Usage:
    python manage.py import_routes                          # Load default routes
    python manage.py import_routes path/to/file.geojson    # Load specific file
    python manage.py import_routes --reset                 # Clear and reload all routes
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib.gis.geos import LineString
from django.core.management.base import BaseCommand, CommandError

from geo.models import Route


class Command(BaseCommand):
    """
    Custom Django management command for importing GeoJSON route files.
    
    Inherits from BaseCommand to integrate with Django's command framework.
    Provides CLI options for file paths and reset functionality.
    """
    help = "Import route GeoJSON files into the Route table."

    def add_arguments(self, parser):
        """
        Define command-line arguments for the import_routes command.
        
        Args:
            parser: Django's argument parser
        """
        parser.add_argument(
            "paths",
            nargs="*",
            help="Optional paths to GeoJSON files. Defaults to geo/data/routes_*.geojson.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing Route records before import.",
        )

    def handle(self, *args, **options):
        """
        Main command handler - executes the route import process.
        
        Steps:
            1. Resolve file paths (user-provided or default from geo/data/)
            2. Optionally delete existing routes (--reset flag)
            3. Iterate through GeoJSON files and extract features
            4. Transform coordinates to WGS84 and create Route objects
            5. Report summary of imported/skipped features
        """
        # Get Django project root directory
        base_dir = Path(settings.BASE_DIR)
        data_dir = base_dir / "geo" / "data"

        # Determine which GeoJSON files to process
        raw_paths = options["paths"]
        if raw_paths:
            # User provided specific file paths - resolve and validate them
            files = []
            for raw in raw_paths:
                candidate = Path(raw)
                # Try: absolute path → project-relative → data directory
                if not candidate.is_absolute():
                    candidate = base_dir / raw
                if not candidate.exists():
                    candidate = data_dir / raw
                if not candidate.exists():
                    raise CommandError(f"GeoJSON file not found: {raw}")
                files.append(candidate)
        else:
            # No paths provided - use default pattern: routes_*.geojson in geo/data/
            files = sorted(data_dir.glob("routes_*.geojson"))

        if not files:
            raise CommandError("No GeoJSON files found to import.")

        # Optional: clear existing routes if --reset flag is set
        if options["reset"]:
            deleted, _ = Route.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing routes."))

        imported = 0
        skipped = 0

        # Process each GeoJSON file
        for geojson_path in files:
            # Load and parse the GeoJSON file
            with geojson_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

            # Extract features array from GeoJSON FeatureCollection
            features = payload.get("features", [])
            if not features:
                self.stdout.write(self.style.WARNING(f"{geojson_path.name}: no features found."))
                continue

            # Process each feature (individual route) in the file
            for index, feature in enumerate(features, start=1):
                # Extract geometry and properties from the feature
                geometry = feature.get("geometry")
                if not geometry:
                    skipped += 1
                    continue

                properties = feature.get("properties") or {}
                # Use feature's name property, or generate a default name
                base_name = (
                    properties.get("Name")
                    or properties.get("name")
                    or f"{geojson_path.stem.replace('_', ' ').title()} Feature {index}"
                )

                # Get geometry type and coordinates
                geom_type = geometry.get("type")
                coordinates = geometry.get("coordinates")
                if not coordinates:
                    skipped += 1
                    continue

                # Normalize coordinates into segments for consistent processing
                # LineString = single segment, MultiLineString = multiple segments
                segments = []
                if geom_type == "LineString":
                    segments = [coordinates]
                elif geom_type == "MultiLineString":
                    segments = [coords for coords in coordinates if len(coords) >= 2]
                else:
                    # Skip unsupported geometry types (Point, Polygon, etc.)
                    self.stdout.write(
                        self.style.WARNING(
                            f"{geojson_path.name} feature {index}: unsupported geometry {geom_type}, skipping."
                        )
                    )
                    skipped += 1
                    continue

                if not segments:
                    skipped += 1
                    continue

                # Create a Route object for each segment
                for segment_idx, segment in enumerate(segments, start=1):
                    # LineString requires minimum 2 coordinate pairs
                    if len(segment) < 2:
                        skipped += 1
                        continue

                    try:
                        # Convert coordinate array to PostGIS LineString with WGS84 (SRID 4326)
                        line = LineString(segment, srid=4326)
                    except TypeError as exc:
                        raise CommandError(
                            f"{geojson_path.name} feature {index} segment {segment_idx}: {exc}"
                        ) from exc

                    # Generate unique name for this route segment
                    name = base_name
                    if len(segments) > 1:
                        # Add segment number if feature contains multiple LineStrings
                        name = f"{base_name} (Segment {segment_idx})"

                    # Create or update the route in the database
                    # update_or_create prevents duplicates if command is run multiple times
                    route, created = Route.objects.update_or_create(
                        name=name,
                        defaults={"path": line},
                    )
                    imported += 1
                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f"{action} route: {name}"))

        if imported == 0:
            raise CommandError("No routes were imported.")

        # Generate and display final import summary
        summary = f"Imported or updated {imported} route segments"
        if skipped:
            summary += f"; skipped {skipped}."
        else:
            summary += "."
        self.stdout.write(self.style.SUCCESS(summary))

