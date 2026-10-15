"""
Database validation script for AI Tools Directory.
Enforces schema rules, referential integrity, unique keys, and data cleanliness.
Uses Python standard library only (zero external dependencies).
"""

import json
import os
import re
import sys
from urllib.parse import urlparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
TOOLS_DIR = os.path.join(DATA_DIR, "tools")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
COLLECTIONS_FILE = os.path.join(DATA_DIR, "collections.json")
TAGS_FILE = os.path.join(DATA_DIR, "tags.json")

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VALID_PRICING_MODELS = {
    "free",
    "freemium",
    "paid",
    "open-source",
    "free-trial",
    "contact-for-pricing",
}

VALID_PLATFORMS = {
    "web",
    "android",
    "ios",
    "windows",
    "macos",
    "linux",
    "api",
    "browser-extension",
}

VALID_STATUSES = {"draft", "published", "archived"}

class ValidationError(Exception):
    pass

def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ValidationError(f"Failed to read/parse JSON from {filepath}: {e}")

def validate_categories_data(categories):
    errors = []
    category_ids = set()
    category_slugs = set()
    subcategory_ids = set()

    if not isinstance(categories, list) or len(categories) == 0:
        errors.append("categories.json must be a non-empty array of category objects")
        return category_ids, subcategory_ids, errors

    for idx, cat in enumerate(categories):
        loc = f"categories[{idx}]"
        for req in ["id", "slug", "name", "shortDescription", "description", "icon", "subcategories"]:
            if req not in cat:
                errors.append(f"{loc}: missing required field '{req}'")

        cat_id = cat.get("id", "")
        if not SLUG_PATTERN.match(cat_id):
            errors.append(f"{loc}: invalid id '{cat_id}', must be lowercase-alphanumeric with hyphens")
        if cat_id in category_ids:
            errors.append(f"{loc}: duplicate category id '{cat_id}'")
        category_ids.add(cat_id)

        cat_slug = cat.get("slug", "")
        if cat_slug != cat_id:
            errors.append(f"{loc}: slug '{cat_slug}' does not match id '{cat_id}'")
        if cat_slug in category_slugs:
            errors.append(f"{loc}: duplicate category slug '{cat_slug}'")
        category_slugs.add(cat_slug)

        subcats = cat.get("subcategories", [])
        if not isinstance(subcats, list):
            errors.append(f"{loc}.subcategories must be a list")
        else:
            for sidx, sub in enumerate(subcats):
                sloc = f"{loc}.subcategories[{sidx}]"
                for sreq in ["id", "name", "slug"]:
                    if sreq not in sub:
                        errors.append(f"{sloc}: missing required subcategory field '{sreq}'")
                sub_id = sub.get("id")
                if sub_id:
                    if sub_id in subcategory_ids:
                        errors.append(f"{sloc}: duplicate subcategory id '{sub_id}'")
                    subcategory_ids.add(sub_id)

    return category_ids, subcategory_ids, errors

def validate_tags_data(tags):
    errors = []
    if not isinstance(tags, list) or len(tags) == 0:
        errors.append("tags.json must be a non-empty array of strings")
        return set(), errors
    tag_set = set()
    for idx, tag in enumerate(tags):
        if not isinstance(tag, str):
            errors.append(f"tags[{idx}] must be a string")
        elif not SLUG_PATTERN.match(tag):
            errors.append(f"tags[{idx}] '{tag}' must match slug pattern")
        elif tag in tag_set:
            errors.append(f"tags[{idx}] duplicate tag '{tag}'")
        tag_set.add(tag)
    return tag_set, errors

def validate_tool_record(tool, filename, valid_categories, valid_tags, valid_subcategories):
    errors = []
    loc = filename

    required_fields = [
        "id", "name", "slug", "shortDescription", "description",
        "categories", "websiteUrl", "pricing", "platforms",
        "status", "createdAt", "updatedAt"
    ]
    for field in required_fields:
        if field not in tool:
            errors.append(f"{loc}: missing required field '{field}'")

    tool_id = tool.get("id", "")
    if not SLUG_PATTERN.match(tool_id):
        errors.append(f"{loc}: invalid id '{tool_id}'")
    expected_filename = f"{tool_id}.json"
    if filename != expected_filename:
        errors.append(f"{loc}: filename must match id (expected {expected_filename})")

    slug = tool.get("slug", "")
    if slug != tool_id:
        errors.append(f"{loc}: slug '{slug}' must match id '{tool_id}'")

    # URL validation
    website = tool.get("websiteUrl", "")
    parsed = urlparse(website)
    if not (parsed.scheme in ("http", "https") and parsed.netloc):
        errors.append(f"{loc}: invalid websiteUrl '{website}'")

    # Categories
    categories = tool.get("categories", [])
    if not isinstance(categories, list) or len(categories) == 0:
        errors.append(f"{loc}: categories must be a non-empty list")
    else:
        for cat in categories:
            if cat not in valid_categories:
                errors.append(f"{loc}: references unknown category '{cat}'")

    # Subcategories (optional)
    subcategories = tool.get("subcategories", [])
    if subcategories:
        for sub in subcategories:
            if sub not in valid_subcategories:
                errors.append(f"{loc}: references unknown subcategory '{sub}'")

    # Tags (optional)
    tags = tool.get("tags", [])
    if tags:
        for tag in tags:
            if tag not in valid_tags:
                errors.append(f"{loc}: references unknown tag '{tag}' (add to tags.json first)")

    # Pricing
    pricing = tool.get("pricing", {})
    if not isinstance(pricing, dict):
        errors.append(f"{loc}: pricing must be an object")
    else:
        model = pricing.get("model")
        if model not in VALID_PRICING_MODELS:
            errors.append(f"{loc}: invalid pricing model '{model}'")
        last_v = pricing.get("lastVerifiedAt")
        if last_v and not DATE_PATTERN.match(last_v):
            errors.append(f"{loc}: pricing.lastVerifiedAt '{last_v}' must be YYYY-MM-DD")

    # Platforms
    platforms = tool.get("platforms", [])
    if not isinstance(platforms, list) or len(platforms) == 0:
        errors.append(f"{loc}: platforms must be a non-empty list")
    else:
        for p in platforms:
            if p not in VALID_PLATFORMS:
                errors.append(f"{loc}: invalid platform '{p}'")

    # Status
    status = tool.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"{loc}: invalid status '{status}'")

    # Dates
    for dfield in ["createdAt", "updatedAt"]:
        dval = tool.get(dfield, "")
        if not DATE_PATTERN.match(dval):
            errors.append(f"{loc}: {dfield} '{dval}' must match YYYY-MM-DD")

    # Verified date
    last_v = tool.get("lastVerifiedAt")
    if last_v and not DATE_PATTERN.match(last_v):
        errors.append(f"{loc}: lastVerifiedAt '{last_v}' must match YYYY-MM-DD")

    return errors

def validate_collections_data(collections, valid_tool_ids):
    errors = []
    collection_ids = set()

    if not isinstance(collections, list):
        errors.append("collections.json must be an array of collection objects")
        return errors

    for idx, col in enumerate(collections):
        loc = f"collections[{idx}]"
        for req in ["id", "slug", "title", "description", "curatorNotes", "toolIds"]:
            if req not in col:
                errors.append(f"{loc}: missing required field '{req}'")

        col_id = col.get("id", "")
        if not SLUG_PATTERN.match(col_id):
            errors.append(f"{loc}: invalid id '{col_id}'")
        if col_id in collection_ids:
            errors.append(f"{loc}: duplicate collection id '{col_id}'")
        collection_ids.add(col_id)

        tool_ids = col.get("toolIds", [])
        if not isinstance(tool_ids, list) or len(tool_ids) == 0:
            errors.append(f"{loc}: toolIds must be a non-empty list")
        else:
            for tid in tool_ids:
                if tid not in valid_tool_ids:
                    errors.append(f"{loc}: references non-existent tool id '{tid}'")

    return errors

def run_validation():
    all_errors = []

    print("--> Validating categories.json...")
    categories = load_json(CATEGORIES_FILE)
    valid_categories, valid_subcategories, cat_errors = validate_categories_data(categories)
    all_errors.extend(cat_errors)

    print("--> Validating tags.json...")
    tags = load_json(TAGS_FILE)
    valid_tags, tag_errors = validate_tags_data(tags)
    all_errors.extend(tag_errors)

    print(f"--> Validating tools in {TOOLS_DIR}...")
    tool_files = [f for f in os.listdir(TOOLS_DIR) if f.endswith(".json")]
    tool_ids = set()
    tools = []

    for f in tool_files:
        filepath = os.path.join(TOOLS_DIR, f)
        tool = load_json(filepath)
        t_errors = validate_tool_record(tool, f, valid_categories, valid_tags, valid_subcategories)
        all_errors.extend(t_errors)

        tid = tool.get("id")
        if tid in tool_ids:
            all_errors.append(f"Duplicate tool id across files: '{tid}'")
        tool_ids.add(tid)
        tools.append(tool)

    # Check cross-tool references (alternatives and relatedTools)
    print("--> Validating cross-tool relationships (alternatives, relatedTools)...")
    for tool in tools:
        for alt in tool.get("alternatives", []):
            if alt not in tool_ids:
                all_errors.append(f"Tool '{tool.get('id')}': alternative '{alt}' does not exist")
        for rel in tool.get("relatedTools", []):
            if rel not in tool_ids:
                all_errors.append(f"Tool '{tool.get('id')}': relatedTool '{rel}' does not exist")

    print("--> Validating collections.json...")
    collections = load_json(COLLECTIONS_FILE)
    col_errors = validate_collections_data(collections, tool_ids)
    all_errors.extend(col_errors)

    if all_errors:
        print(f"\n[FAIL] Validation found {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  * {err}")
        return False
    else:
        print(f"\n[SUCCESS] Dataset is valid! (Categories: {len(valid_categories)}, Tags: {len(valid_tags)}, Tools: {len(tools)}, Collections: {len(collections)})")
        return True

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
