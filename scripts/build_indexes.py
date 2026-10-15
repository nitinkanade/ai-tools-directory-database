"""
Index and manifest generator for AI Tools Directory.
Generates published artifacts in public/data/ with sha256 checksums.
Uses Python standard library only.
"""

import datetime
import hashlib
import json
import os
import shutil
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
TOOLS_DIR = os.path.join(DATA_DIR, "tools")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "public", "data")

SCHEMA_VERSION = "1.0.0"
MIN_APP_VERSION = "1.0.0"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_public_dataset():
    print("--> Preparing public/data directory...")
    if os.path.exists(PUBLIC_DATA_DIR):
        shutil.rmtree(PUBLIC_DATA_DIR)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(PUBLIC_DATA_DIR, "tools"), exist_ok=True)
    os.makedirs(os.path.join(PUBLIC_DATA_DIR, "tools", "by-category"), exist_ok=True)

    # 1. Copy categories.json
    with open(os.path.join(DATA_DIR, "categories.json"), "r", encoding="utf-8") as f:
        categories = json.load(f)
    with open(os.path.join(PUBLIC_DATA_DIR, "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    # 2. Copy tags.json
    with open(os.path.join(DATA_DIR, "tags.json"), "r", encoding="utf-8") as f:
        tags = json.load(f)
    with open(os.path.join(PUBLIC_DATA_DIR, "tags.json"), "w", encoding="utf-8") as f:
        json.dump(tags, f, indent=2, ensure_ascii=False)

    # 3. Copy collections.json
    with open(os.path.join(DATA_DIR, "collections.json"), "r", encoding="utf-8") as f:
        collections = json.load(f)
    with open(os.path.join(PUBLIC_DATA_DIR, "collections.json"), "w", encoding="utf-8") as f:
        json.dump(collections, f, indent=2, ensure_ascii=False)

    # 4. Process tools
    tool_files = sorted([f for f in os.listdir(TOOLS_DIR) if f.endswith(".json")])
    compact_tools = []
    search_index = []
    category_tool_map = {c["id"]: [] for c in categories}
    published_count = 0

    for f in tool_files:
        with open(os.path.join(TOOLS_DIR, f), "r", encoding="utf-8") as tf:
            tool = json.load(tf)

        # Exclude drafts and archived records
        if tool.get("status") != "published":
            continue

        published_count += 1

        # Write per-tool public file
        tool_dest = os.path.join(PUBLIC_DATA_DIR, "tools", f"{tool['slug']}.json")
        with open(tool_dest, "w", encoding="utf-8") as out_f:
            json.dump(tool, out_f, indent=2, ensure_ascii=False)

        # Add to compact list
        compact = {
            "id": tool["id"],
            "name": tool["name"],
            "slug": tool["slug"],
            "shortDescription": tool["shortDescription"],
            "categories": tool["categories"],
            "subcategories": tool.get("subcategories", []),
            "tags": tool.get("tags", []),
            "websiteUrl": tool["websiteUrl"],
            "pricing": tool["pricing"],
            "platforms": tool["platforms"],
            "isOpenSource": tool.get("isOpenSource"),
            "isFeatured": tool.get("isFeatured", False),
            "status": tool["status"],
            "lastVerifiedAt": tool.get("lastVerifiedAt"),
            "createdAt": tool["createdAt"],
            "updatedAt": tool["updatedAt"],
        }
        compact_tools.append(compact)

        # Add to search index
        search_doc = {
            "id": tool["id"],
            "name": tool["name"],
            "slug": tool["slug"],
            "shortDescription": tool["shortDescription"],
            "categories": tool["categories"],
            "tags": tool.get("tags", []),
            "features": tool.get("features", []),
            "pricingModel": tool["pricing"]["model"],
            "platforms": tool["platforms"],
            "isOpenSource": tool.get("isOpenSource"),
            "isFeatured": tool.get("isFeatured", False),
        }
        search_index.append(search_doc)

        # Add to category maps
        for cat in tool["categories"]:
            if cat in category_tool_map:
                category_tool_map[cat].append(tool["id"])

    # Write tools/index.json
    with open(os.path.join(PUBLIC_DATA_DIR, "tools", "index.json"), "w", encoding="utf-8") as f:
        json.dump(compact_tools, f, indent=2, ensure_ascii=False)

    # Write search-index.json
    with open(os.path.join(PUBLIC_DATA_DIR, "search-index.json"), "w", encoding="utf-8") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)

    # Write per-category index files
    for cat_id, t_ids in category_tool_map.items():
        with open(os.path.join(PUBLIC_DATA_DIR, "tools", "by-category", f"{cat_id}.json"), "w", encoding="utf-8") as f:
            json.dump({"categoryId": cat_id, "toolIds": t_ids, "count": len(t_ids)}, f, indent=2)

    # Compute manifest file hashes
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    dataset_version = f"{now_utc.strftime('%Y.%m.%d')}-v1"

    file_manifest = {}
    for root, _, files in os.walk(PUBLIC_DATA_DIR):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, PUBLIC_DATA_DIR).replace("\\", "/")
            if rel_path == "manifest.json":
                continue
            file_manifest[rel_path] = {
                "path": f"/data/{rel_path}",
                "sha256": compute_sha256(full_path),
                "bytes": os.path.getsize(full_path),
            }

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "datasetVersion": dataset_version,
        "generatedAt": now_utc.isoformat(),
        "totalTools": published_count,
        "totalCategories": len(categories),
        "totalCollections": len(collections),
        "minAppVersion": MIN_APP_VERSION,
        "files": file_manifest,
    }

    manifest_path = os.path.join(PUBLIC_DATA_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Public dataset generated at {PUBLIC_DATA_DIR}")
    print(f"  Published Tools: {published_count}")
    print(f"  Categories: {len(categories)}")
    print(f"  Collections: {len(collections)}")
    print(f"  Total published files in manifest: {len(file_manifest)}")
    return True

if __name__ == "__main__":
    success = build_public_dataset()
    sys.exit(0 if success else 1)
