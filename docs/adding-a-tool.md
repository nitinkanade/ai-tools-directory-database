# Standard Operating Procedure (SOP): Adding a New AI Tool

Follow this procedure to research, verify, author, validate, and publish a new AI tool record.

## Step-by-Step Instructions

### Step 1: Research and Fact Verification
1. Visit the tool's official website and terms/pricing page.
2. Verify:
   - Official product name and exact domain URL.
   - Pricing tiers (Is there a real free tier? What are the usage caps?).
   - Supported client platforms (Web, Android, iOS, Windows, Mac, Linux, API).
   - Open source status (Confirm OSI-approved license on GitHub/GitLab).
   - Key capabilities and factual limitations.

### Step 2: Determine Identifier and Slug
- Choose a unique, lowercase, hyphenated slug: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Example: `claude-code`, `stable-diffusion-webui`.
- Verify the ID is not already used in `data/tools/`.

### Step 3: Check Categories and Tags
- Select at least one category from `data/categories.json`.
- Review existing tags in `data/tags.json`. If a new tag is necessary, add it to `data/tags.json` first.

### Step 4: Create Tool JSON Record
Create `data/tools/<slug>.json`. Use the sample template below:

```json
{
  "id": "my-tool",
  "name": "My Tool",
  "slug": "my-tool",
  "shortDescription": "Concise factual summary between 10 and 220 characters.",
  "description": "Comprehensive explanation of what the tool does, how it works, and key architecture details.",
  "categories": ["coding-development"],
  "subcategories": ["code-assistants"],
  "tags": ["coding", "autocomplete", "developer-tools"],
  "websiteUrl": "https://example.com",
  "pricing": {
    "model": "freemium",
    "details": "Free tier with 1,000 monthly credits; Pro at $15/mo.",
    "lastVerifiedAt": "2026-10-15"
  },
  "platforms": ["web", "windows", "macos"],
  "isOpenSource": false,
  "sourceCodeUrl": null,
  "isFeatured": false,
  "status": "published",
  "features": [
    "Feature one description",
    "Feature two description"
  ],
  "useCases": [
    "Practical use case one",
    "Practical use case two"
  ],
  "alternatives": ["github-copilot"],
  "relatedTools": ["cursor"],
  "languageSupport": ["English", "multilingual"],
  "accountRequired": true,
  "limitations": [
    "Daily quota caps on free accounts"
  ],
  "lastVerifiedAt": "2026-10-15",
  "sourceReferences": ["https://example.com/pricing"],
  "createdAt": "2026-10-15",
  "updatedAt": "2026-10-15",
  "seo": {
    "title": "My Tool — AI Code Generator & Assistant",
    "description": "Explore features, pricing, and alternatives for My Tool."
  }
}
```

### Step 5: Run Automated Validation
Run the validator from the database root:

```bash
python scripts/validate.py
```

If validation reports errors (e.g., broken alternative links, missing tags, bad date format), correct them until `[SUCCESS]` is reported.

### Step 6: Generate Published Indexes
Build the updated public dataset:

```bash
python scripts/build_indexes.py
```

### Step 7: Run Regression Tests
Verify test suite:

```bash
python -m unittest discover tests
```

### Step 8: Commit and Deploy
Commit changes to Git:
```bash
git add data/ public/
git commit -m "feat(tools): add my-tool listing"
git push origin main
```
The GitHub Actions workflow will validate and deploy the updated dataset to GitHub Pages. The Android app and website will immediately reflect the new tool upon next data sync!

---

## Common Mistakes to Avoid

1. **Fabricating Ratings or Statistics**: Never invent star ratings, user numbers, or popularity ranks.
2. **Broken Cross-References**: Listing an alternative tool ID that does not exist in `data/tools/`.
3. **Invalid Tag References**: Using tags not present in `data/tags.json`.
4. **Filename vs Slug Mismatch**: Filename must exactly match `<slug>.json`.
5. **Marking Closed Source as Open Source**: Only set `isOpenSource: true` if an open-source license repository exists.
