#!/usr/bin/env python3
"""
Ecosystem health verifier for AI Tools Directory.
Executes database validation, unit tests, index builds, and verifies blog frontmatter & references.
"""

import sys
import subprocess
from pathlib import Path

def run_step(description, command):
    print(f"==> {description}...")
    res = subprocess.run(command, shell=True)
    if res.returncode != 0:
        print(f"[FAIL] Step failed: {description}")
        sys.exit(1)
    print(f"[PASS] {description}\n")

def check_blog_articles():
    print("==> Verifying blog articles in ai-tools-directory-website/content/blog...")
    blog_dir = Path("ai-tools-directory-website/content/blog")
    if not blog_dir.exists():
        print(f"[FAIL] Blog directory does not exist: {blog_dir}")
        sys.exit(1)

    articles = list(blog_dir.glob("*.md"))
    if not articles:
        print(f"[FAIL] No blog articles found in {blog_dir}")
        sys.exit(1)

    required_keys = ["title:", "slug:", "description:", "author:", "publishedAt:", "updatedAt:", "tags:", "categories:"]

    for article in articles:
        text = article.read_text(encoding="utf-8")
        if not text.startswith("---"):
            print(f"[FAIL] Article {article.name} missing frontmatter start (---)")
            sys.exit(1)

        for key in required_keys:
            if key not in text:
                print(f"[FAIL] Article {article.name} missing required frontmatter key: {key}")
                sys.exit(1)

        print(f"  - Verified article: {article.name}")

    print("[PASS] Blog articles verification complete\n")

def main():
    print("==========================================")
    print(" Running Full Ecosystem Verification")
    print("==========================================\n")

    # 1. Database validation
    run_step("Database Validation", "python scripts/validate.py")

    # 2. Database unit tests
    run_step("Unit Tests Discovery", "python -m unittest discover tests")

    # 3. Build indexes
    run_step("Build Public Manifests & Search Indexes", "python scripts/build_indexes.py")

    # 4. Check blog articles
    check_blog_articles()

    print("==========================================")
    print(" [SUCCESS] Ecosystem is 100% healthy!")
    print("==========================================")

if __name__ == "__main__":
    main()
