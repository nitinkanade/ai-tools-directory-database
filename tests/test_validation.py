"""
Test suite for database validation, referential integrity, and manifest generation.
"""

import json
import os
import unittest
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from validate import (
    run_validation,
    validate_tool_record,
    validate_categories_data,
    validate_tags_data,
    validate_collections_data,
    load_json,
)
from build_indexes import compute_sha256

class TestDatabaseValidation(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(BASE_DIR, "data")
        self.public_dir = os.path.join(BASE_DIR, "public", "data")
        self.categories = load_json(os.path.join(self.data_dir, "categories.json"))
        self.tags = load_json(os.path.join(self.data_dir, "tags.json"))
        self.collections = load_json(os.path.join(self.data_dir, "collections.json"))
        self.cat_ids, self.subcat_ids, _ = validate_categories_data(self.categories)
        self.tag_set, _ = validate_tags_data(self.tags)

    def test_live_dataset_passes_validation(self):
        """Current live dataset must be 100% valid with 0 errors."""
        self.assertTrue(run_validation())

    def test_rejects_missing_required_fields(self):
        broken_tool = {
            "id": "broken-tool",
            "name": "Broken",
            # missing slug, shortDescription, etc.
        }
        errs = validate_tool_record(broken_tool, "broken-tool.json", self.cat_ids, self.tag_set, self.subcat_ids)
        self.assertTrue(len(errs) > 0)
        self.assertTrue(any("missing required field 'slug'" in e for e in errs))

    def test_rejects_invalid_pricing_model(self):
        broken_tool = {
            "id": "broken-pricing",
            "name": "Broken Pricing",
            "slug": "broken-pricing",
            "shortDescription": "Test short description for broken pricing.",
            "description": "Test detailed description of the broken pricing tool for validation.",
            "categories": ["chatbots-assistants"],
            "websiteUrl": "https://example.com",
            "pricing": {"model": "super-expensive-tier"},
            "platforms": ["web"],
            "status": "published",
            "createdAt": "2026-01-01",
            "updatedAt": "2026-01-01",
        }
        errs = validate_tool_record(broken_tool, "broken-pricing.json", self.cat_ids, self.tag_set, self.subcat_ids)
        self.assertTrue(any("invalid pricing model" in e for e in errs))

    def test_rejects_unknown_category(self):
        broken_tool = {
            "id": "broken-cat",
            "name": "Broken Category",
            "slug": "broken-cat",
            "shortDescription": "Test short description for broken category.",
            "description": "Test detailed description of the broken category tool for validation.",
            "categories": ["non-existent-fantasy-category"],
            "websiteUrl": "https://example.com",
            "pricing": {"model": "free"},
            "platforms": ["web"],
            "status": "published",
            "createdAt": "2026-01-01",
            "updatedAt": "2026-01-01",
        }
        errs = validate_tool_record(broken_tool, "broken-cat.json", self.cat_ids, self.tag_set, self.subcat_ids)
        self.assertTrue(any("unknown category" in e for e in errs))

    def test_rejects_duplicate_category_id(self):
        dup_cats = [
            {
                "id": "duplicate-id",
                "slug": "duplicate-id",
                "name": "Cat 1",
                "shortDescription": "Desc 1234567890",
                "description": "Desc long enough 123456789012345",
                "icon": "chat",
                "subcategories": [],
            },
            {
                "id": "duplicate-id",
                "slug": "duplicate-id",
                "name": "Cat 2",
                "shortDescription": "Desc 1234567890",
                "description": "Desc long enough 123456789012345",
                "icon": "chat",
                "subcategories": [],
            },
        ]
        _, _, errs = validate_categories_data(dup_cats)
        self.assertTrue(any("duplicate category id" in e for e in errs))

    def test_manifest_integrity_and_hashes(self):
        """Verify manifest.json in public/data accurately reflects files on disk."""
        manifest_path = os.path.join(self.public_dir, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path), "manifest.json must exist in public/data")
        manifest = load_json(manifest_path)

        self.assertIn("files", manifest)
        self.assertIn("datasetVersion", manifest)
        self.assertIn("schemaVersion", manifest)

        for rel_path, meta in manifest["files"].items():
            full_disk_path = os.path.join(self.public_dir, rel_path.replace("/", os.sep))
            self.assertTrue(os.path.exists(full_disk_path), f"File {rel_path} listed in manifest missing on disk")
            computed_hash = compute_sha256(full_disk_path)
            self.assertEqual(meta["sha256"], computed_hash, f"Hash mismatch for {rel_path}")
            self.assertEqual(meta["bytes"], os.path.getsize(full_disk_path))

if __name__ == "__main__":
    unittest.main()
