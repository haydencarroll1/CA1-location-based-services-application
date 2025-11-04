# Django Migrations Explained

## Overview

**Migrations** are Django's version control system for your database schema. They track every change you make to your database structure over time, allowing you to:

- Apply changes in development
- Deploy to production safely
- Rollback if something goes wrong
- Collaborate without database conflicts

Think of migrations like **Git for your database schema** - each migration is a "commit" of database changes.

---

## Your 3 Migration Files

Your project has a progression of database changes:

```
┌─────────────────────────────────────────────────────────────┐
│ Migration Timeline                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 0001_initial.py (Oct 26, 2025)                             │
│ └─ Create 3 tables: Amenity, Area, Route                   │
│                                                             │
│     ↓ (depends on)                                          │
│                                                             │
│ 0002_add_spatial_indexes.py (Nov 1, 2025)                  │
│ └─ Add GiST spatial indexes on geometry columns            │
│                                                             │
│     ↓ (depends on)                                          │
│                                                             │
│ 0003_amenity_source_ref.py (Nov 1, 2025)                   │
│ └─ Add source_ref field to Amenity model                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Migration 0001: Initial Setup

**File:** `0001_initial.py`

**Purpose:** Create the initial database schema (the three models)

**What it does:**

```python
# Creates these tables:

CREATE TABLE geo_amenity (
    id BIGINT PRIMARY KEY,
    name VARCHAR(120),
    category VARCHAR(20),
    location GEOMETRY(Point, 4326),      # ← Spatial column
    description TEXT
);

CREATE TABLE geo_area (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    boundary GEOMETRY(Polygon, 4326)     # ← Spatial column
);

CREATE TABLE geo_route (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    path GEOMETRY(LineString, 4326)      # ← Spatial column
);
```

**When it runs:**
- First time you run `python manage.py migrate`
- Creates all three tables from scratch

**Python representation:**
```python
migrations.CreateModel(
    name='Amenity',
    fields=[
        ('id', models.BigAutoField(...)),
        ('name', models.CharField(max_length=120)),
        ('category', models.CharField(...)),
        ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
        ('description', models.TextField(...)),
    ],
),
migrations.CreateModel(
    name='Area',
    fields=[...],
),
migrations.CreateModel(
    name='Route',
    fields=[...],
),
```

**Status:** ✅ APPLIED (tables exist in your database)

---

## Migration 0002: Add Spatial Indexes

**File:** `0002_add_spatial_indexes.py`

**Purpose:** Optimize spatial queries by adding database indexes

**What it does:**

```sql
CREATE INDEX geo_amenity_location_gix ON geo_amenity USING GIST(location);
CREATE INDEX geo_area_boundary_gix ON geo_area USING GIST(boundary);
CREATE INDEX geo_route_path_gix ON geo_route USING GIST(path);
```

### Why Indexes Matter

**Without indexes:**
```
Query: Find amenities near (−6.26, 53.35)
Database: Scan ALL rows in geo_amenity table
Time: O(n) - linear scan, SLOW ❌
```

**With GiST spatial indexes:**
```
Query: Find amenities near (−6.26, 53.35)
Database: Use spatial tree to narrow candidates
Time: O(log n) - tree lookup, FAST ✅
Speedup: 1000x faster for large datasets!
```

### What is GiST?

**GiST** = Generalized Search Tree
- PostGIS spatial index type
- Works with geometry columns
- Organized geometries in a tree structure
- Perfect for "nearest neighbor" queries

### Dependency Chain

```python
class Migration(migrations.Migration):

    dependencies = [
        ("geo", "0001_initial"),    # ← Must run 0001 first!
    ]
```

**Why?** The index needs the `geo_amenity` table to exist first. You can't create an index on a table that doesn't exist!

**Status:** ✅ APPLIED (indexes created, queries now fast)

---

## Migration 0003: Add Source Reference

**File:** `0003_amenity_source_ref.py`

**Purpose:** Add a new field to track data source (e.g., OpenStreetMap)

**What it does:**

```python
migrations.AddField(
    model_name='amenity',
    name='source_ref',
    field=models.CharField(blank=True, max_length=64, null=True, unique=True),
)
```

**Adds column to table:**

```sql
ALTER TABLE geo_amenity
ADD COLUMN source_ref VARCHAR(64) UNIQUE;
```

**Result:** `geo_amenity` table now has a new column

```
┌─────────────────────────────────────────────┐
│ geo_amenity table (BEFORE migration 0003)   │
├─────────────────────────────────────────────┤
│ id | name    | category | location | desc  │
├─────────────────────────────────────────────┤
│ 1  | Café    | cafe     | POINT... | ...   │
│ 2  | Park    | park     | POINT... | ...   │
└─────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ geo_amenity table (AFTER migration 0003)               │
├────────────────────────────────────────────────────────┤
│ id | name   | category | location | desc | source_ref │
├────────────────────────────────────────────────────────┤
│ 1  | Café   | cafe     | POINT... | ...  | NULL       │
│ 2  | Park   | park     | POINT... | ...  | NULL       │
└────────────────────────────────────────────────────────┘
     ↑ New column added (empty for old records)
```

### Why This Field?

The `source_ref` field lets you track:
- Which amenities came from OpenStreetMap
- Which came from your sample data
- Useful for data audit trails and updates

**Example values:**
```
source_ref = "osm_123456"        # From OSM with ID 123456
source_ref = "sample_001"        # From sample.json
source_ref = "manual_entry_2025" # Manually added
```

### Dependency Chain

```python
dependencies = [
    ('geo', '0002_add_spatial_indexes'),  # ← Must run 0002 first!
]
```

**Status:** ✅ APPLIED (column added to table)

---

## How Migrations Are Tracked

Django creates a special table to record which migrations have been applied:

```sql
SELECT * FROM django_migrations;
```

Output:
```
│ id │ app   │ name                          │ applied                 │
├────┼───────┼───────────────────────────────┼─────────────────────────┤
│ 1  │ geo   │ 0001_initial                  │ 2025-10-26 17:40:00     │
│ 2  │ geo   │ 0002_add_spatial_indexes      │ 2025-11-01 18:30:00     │
│ 3  │ geo   │ 0003_amenity_source_ref       │ 2025-11-01 18:31:00     │
└────┴───────┴───────────────────────────────┴─────────────────────────┘
```

**Purpose:** Django knows which migrations to skip on next run

---

## Migration Workflow

### When You Change a Model

**Before migration:**
```python
# geo/models.py
class Amenity(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    location = models.PointField(srid=4326)
```

**Make change:**
```python
# geo/models.py
class Amenity(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    location = models.PointField(srid=4326)
    source_ref = models.CharField(...)  # ← NEW FIELD
```

**Create migration:**
```bash
python manage.py makemigrations geo
```

**Output:**
```
Migrations for 'geo':
  geo/migrations/0003_amenity_source_ref.py
    - Add field source_ref to amenity
```

**Apply migration:**
```bash
python manage.py migrate
```

**Result:** Database table updated with new column

---

## Dependency Graph

Your migrations form a chain:

```
0001_initial
    ↓
    └─ Creates tables (Amenity, Area, Route)
    
0002_add_spatial_indexes
    ↓ (depends on 0001)
    └─ Creates indexes on those tables
    
0003_amenity_source_ref
    ↓ (depends on 0002)
    └─ Adds field to Amenity table
```

**Each migration depends on the previous one:**
- Can't run 0002 without 0001 (no tables to index!)
- Can't run 0003 without 0002 (can't add field to non-existent table?)

**Why?** Ensures database consistency and proper ordering

---

## Migration Files: What's Inside

### Operation Types

Your migrations use:

| Operation | Purpose | Example |
|-----------|---------|---------|
| `CreateModel` | Create new table | 0001 creates Amenity, Area, Route |
| `AddField` | Add column to table | 0003 adds source_ref |
| `RunSQL` | Execute raw SQL | 0002 creates indexes |
| `RemoveField` | Delete column | (Not used, but available) |
| `AlterField` | Modify column | (Not used, but available) |
| `DeleteModel` | Drop table | (Not used, but available) |

### Reverse SQL

Each migration can be reversed:

```python
migrations.RunSQL(
    sql="""CREATE INDEX...""",
    reverse_sql="""DROP INDEX..."""  # ← Undo operation
)
```

**Rollback example:**
```bash
# Undo last migration
python manage.py migrate geo 0002

# Database reverts to state after 0002
# Removes the source_ref column added by 0003
```

---

## Real-World Scenario

### Scenario: You broke production!

```
Production database state:
- 0001_initial ✓
- 0002_add_spatial_indexes ✓
- 0003_amenity_source_ref ✓

You made a bad change in 0004_bad_migration.py

Quick fix: Rollback
python manage.py migrate geo 0003

Production now reverts to state before 0004
Customers don't lose data! ✓
```

---

## Common Migration Commands

```bash
# See all migrations
python manage.py showmigrations

# Output:
# geo
#  [X] 0001_initial
#  [X] 0002_add_spatial_indexes
#  [X] 0003_amenity_source_ref

# Create migration after model change
python manage.py makemigrations geo

# Apply all pending migrations
python manage.py migrate

# Apply specific migration
python manage.py migrate geo 0002

# Rollback to specific migration
python manage.py migrate geo 0001

# Show SQL for migration (preview changes)
python manage.py sqlmigrate geo 0003
```

---

## Your Migration Timeline

```
Oct 26, 2025 - 17:40
│
└─ 0001_initial.py
   Created 3 tables with spatial columns
   - Amenity (location: Point)
   - Area (boundary: Polygon)
   - Route (path: LineString)

Nov 1, 2025 - 18:30
│
└─ 0002_add_spatial_indexes.py
   Added GiST indexes for fast queries
   - geo_amenity_location_gix
   - geo_area_boundary_gix
   - geo_route_path_gix

Nov 1, 2025 - 18:31
│
└─ 0003_amenity_source_ref.py
   Added source_ref column to Amenity
   Tracks data source (OSM, samples, manual)
```

---

## Summary Table

| Migration | When | What | Why |
|-----------|------|------|-----|
| **0001_initial** | Oct 26 | Create tables | Define database schema |
| **0002_add_spatial_indexes** | Nov 1 | Add indexes | Optimize spatial queries |
| **0003_amenity_source_ref** | Nov 1 | Add column | Track data source |

---

## Key Takeaways

1. **Migrations = Git for databases** - Track all schema changes
2. **Dependency chain** - Each migration depends on previous ones
3. **Reversible** - Can rollback to any point in time
4. **Auto-generated** - Django creates them from model changes
5. **Version control** - Migrations are code, tracked in Git
6. **Production-safe** - Apply migrations safely in production

Your 3 migrations represent the evolution of your database schema from initial design → performance optimization → feature expansion.

