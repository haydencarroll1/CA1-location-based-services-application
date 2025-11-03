from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("geo", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS geo_area_boundary_gix
                ON geo_area USING GIST(boundary);

                CREATE INDEX IF NOT EXISTS geo_route_path_gix
                ON geo_route USING GIST(path);

                CREATE INDEX IF NOT EXISTS geo_amenity_location_gix
                ON geo_amenity USING GIST(location);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS geo_area_boundary_gix;
                DROP INDEX IF EXISTS geo_route_path_gix;
                DROP INDEX IF EXISTS geo_amenity_location_gix;
            """,
        ),
    ]
