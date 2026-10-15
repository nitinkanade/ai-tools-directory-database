# AI Tools Directory — Static JSON Database

The version-controlled single source of truth for the **AI Tools Directory** ecosystem.

## Features

- **Standardized Data Schemas**: JSON Schema (draft 2020-12) for tools, categories, collections, and release manifests.
- **Strict Automated Validation**: Enforces uniqueness of IDs/slugs, referential integrity across categories, valid URLs, pricing enums, and ISO dates.
- **Zero Paid Infrastructure**: Serves statically via GitHub Pages with HTTPS edge caching.
- **Index & Manifest Generator**: Automatically compiles `tools/index.json`, search indexes, category listings, and sha256 checksums.

## Quick Start & Local Commands

```bash
# 1. Validate dataset
python scripts/validate.py

# 2. Build public indexes and manifest into public/data/
python scripts/build_indexes.py

# 3. Run automated tests
python -m unittest discover tests
```

## Documentation

- [Data Model & Field Specification](docs/data-model.md)
- [SOP: Adding a New AI Tool](docs/adding-a-tool.md)
- [SOP: Managing Categories and Tags](docs/managing-categories-and-tags.md)
- [Schema Versioning & Migrations](docs/schema-migrations.md)
- [Publishing & Hosting Guide](docs/publishing-and-hosting.md)
