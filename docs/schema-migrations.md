# Schema Versioning & Migration Policy

## Versioning Semantics

The AI Tools Directory dataset follows Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **Major (e.g., 2.0.0)**: Breaking changes to JSON structure (e.g., renaming a required property, changing data types, removing critical top-level structures). Older mobile apps unable to parse the new structure must inspect `manifest.minAppVersion` and gracefully decline incompatible datasets, retaining their last valid local cache.
- **Minor (e.g., 1.1.0)**: Non-breaking backward-compatible schema additions (e.g., adding an optional field such as `discordCommunityUrl` or a new platform enum value). Modern clients will parse it; older clients safely ignore unknown properties.
- **Patch / Dataset Version (e.g., 2026.10.15-v1)**: Content additions, pricing updates, new tools, and bug fixes without schema alterations.

## Client Compatibility Contract

1. **Permissive Ingestion**: All Dart and JavaScript client models are built to tolerate unknown keys without throwing unhandled exceptions.
2. **Explicit Nullability**: Unknown or unverified fields are stored as `null` rather than omitted or guessed.
3. **Atomic Cache Update**: The Android client checks `manifest.json`. If `schemaVersion` is compatible and `datasetVersion` is newer, it downloads `tools/index.json` and verifies parsing **before** overwriting the cached file on disk. If network drops or parsing fails, the previous cache remains 100% intact.
