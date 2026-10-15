# SOP: Managing Categories and Tags

This document outlines how to safely introduce, rename, merge, or deprecate categories and tags without breaking existing mobile clients, website routes, or search indexes.

## 1. Adding a New Category

1. Open `data/categories.json`.
2. Append a new category object adhering to `schemas/category.schema.json`:
   ```json
   {
     "id": "new-category-slug",
     "slug": "new-category-slug",
     "name": "New Category Name",
     "shortDescription": "10-200 chars summary",
     "description": "20-1000 chars in-depth scope",
     "icon": "material_icon_name",
     "featured": false,
     "subcategories": []
   }
   ```
3. Run `python scripts/validate.py` to ensure uniqueness.
4. Run `python scripts/build_indexes.py`.
5. Mobile clients and the website will automatically discover the category on their next manifest update.

## 2. Renaming or Merging Categories

> [!WARNING]
> Renaming an `id` or `slug` is a breaking change for existing URLs and client filter bookmarks. Follow the deprecation procedure below.

### Deprecation & Migration Procedure:
1. **Never mutate an active ID directly**.
2. Create the new target category in `data/categories.json`.
3. Update all affected tool JSON files in `data/tools/` to include the new category in their `categories` list.
4. If keeping the old category temporarily for backward compatibility, leave it in `categories.json` until client version analytics show adoption.
5. In the website static generator, generate an HTTP-EQUIV 301 redirect or meta refresh for `/category/<old-slug>/` pointing to `/category/<new-slug>/`.

## 3. Adding and Managing Tags

- Tags live in `data/tags.json` as a controlled, alphabetical lowercase list.
- To add a tag: add the slug string to `data/tags.json`.
- When renaming a tag, run a global search across `data/tools/*.json` to replace occurrences.
- Run `python scripts/validate.py` to verify that no tool references a retired tag.
