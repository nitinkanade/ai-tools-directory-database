# AI Tools Directory — Data Model Specification (v1.0.0)

## Overview

The database project is the **single source of truth** for all tool records, category taxonomies, tag registries, and curated collections in the AI Tools Directory ecosystem.

All data is stored in standard JSON files under `data/`, validated against JSON Schemas in `schemas/`, and transformed into a clean public distribution under `public/data/` for consumption by both the static website and the Flutter Android application.

## Directory Structure

```
ai-tools-directory-database/
├── data/
│   ├── categories.json         # Taxonomy of 20 categories + subcategories
│   ├── tags.json               # Controlled vocabulary of standardized tags
│   ├── collections.json        # Curated editorial collections
│   └── tools/                  # Individual tool records (one JSON file per tool)
│       ├── chatgpt.json
│       ├── claude.json
│       └── ...
├── schemas/
│   ├── tool.schema.json        # Draft 2020-12 schema for tool records
│   ├── category.schema.json    # Schema for categories
│   ├── collection.schema.json  # Schema for collections
│   └── manifest.schema.json    # Schema for published release manifest
├── scripts/
│   ├── validate.py             # Validation and referential integrity checker
│   ├── build_indexes.py        # Generates public/data artifacts + manifest
│   └── seed_tools.py           # Helper for initial data seeding
├── tests/
│   └── test_validation.py      # Automated regression test suite
└── public/data/                # Build output hosted on GitHub Pages
    ├── manifest.json           # Root dataset manifest with sha256 checksums
    ├── categories.json         # Public categories endpoint
    ├── tags.json               # Public tags list
    ├── collections.json        # Public collections endpoint
    ├── search-index.json       # Compact search documents for fast client search
    └── tools/
        ├── index.json          # Compact array of all published tools
        ├── by-category/*.json  # Tool ID mappings per category
        └── *.json              # Individual full tool records
```

## Schema Reference: Tool Record

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Lowercase alphanumeric slug with hyphens (e.g., `github-copilot`). Immutable. |
| `name` | string | Yes | Human-readable tool title (2–100 chars). |
| `slug` | string | Yes | URL-friendly slug, strictly matches `id`. |
| `shortDescription` | string | Yes | 10–220 character concise summary for cards and meta descriptions. |
| `description` | string | Yes | 30–3000 character detailed description. |
| `categories` | array[string] | Yes | At least 1 valid category ID from `categories.json`. First element is primary category. |
| `subcategories` | array[string] | No | Optional subcategory identifiers. |
| `tags` | array[string] | No | Keywords from `tags.json`. |
| `websiteUrl` | string | Yes | Valid HTTPS/HTTP official URL. |
| `pricing` | object | Yes | `{ model: string, details?: string, lastVerifiedAt?: string }`. |
| `platforms` | array[string] | Yes | Enum: `web`, `android`, `ios`, `windows`, `macos`, `linux`, `api`, `browser-extension`. |
| `isOpenSource` | boolean \| null | No | `true` if OSI-approved license, `false` if closed, `null` if unverified. |
| `sourceCodeUrl` | string \| null | No | Repository URL if open source. |
| `isFeatured` | boolean | No | Default `false`. Curated editorial showcase flag. |
| `status` | string | Yes | Enum: `draft`, `published`, `archived`. Only `published` tools appear in public indexes. |
| `features` | array[string] | No | 3–10 key capabilities. |
| `useCases` | array[string] | No | Practical use cases. |
| `alternatives` | array[string] | No | List of tool IDs of direct alternatives (referential integrity enforced). |
| `relatedTools` | array[string] | No | List of tool IDs of complementary tools (referential integrity enforced). |
| `languageSupport`| array[string] | No | Supported natural or programming languages. |
| `accountRequired`| boolean \| null | No | Account requirement for basic usage. |
| `limitations` | array[string] | No | Factual limitations or usage constraints. |
| `lastVerifiedAt` | string \| null | No | `YYYY-MM-DD` date when facts were verified by editor. |
| `sourceReferences`| array[string] | No | URLs used to verify pricing/features. |
| `createdAt` | string | Yes | `YYYY-MM-DD`. |
| `updatedAt` | string | Yes | `YYYY-MM-DD`. |
| `seo` | object | No | `{ title?: string, description?: string }`. |

## Allowed Enums

- **Pricing Models**:
  - `free`: Completely free to use with no hidden fees.
  - `freemium`: Free tier available with optional paid upgrades.
  - `paid`: Subscription or one-time license required.
  - `open-source`: Free, open-source software (may incur self-hosting hardware costs).
  - `free-trial`: Paid service offering a limited-time or limited-credit trial.
  - `contact-for-pricing`: Enterprise bespoke contracts.
- **Publication Status**:
  - `draft`: In review; excluded from public listings.
  - `published`: Verified and active in public directories.
  - `archived`: Deprecated or discontinued tool; preserved in Git, excluded from public feeds.
