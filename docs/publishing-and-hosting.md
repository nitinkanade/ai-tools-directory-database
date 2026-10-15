# Publishing & Static Hosting on GitHub Pages

## Zero-Cost Hosting Architecture

The dataset is publicly hosted on GitHub Pages under the repository's `gh-pages` branch or root `public/` directory:

- Base URL: `https://<owner>.github.io/<repo>/data/`
- All assets are served over HTTPS with standard CDN edge caching.
- Zero server-side API or database runtime required.
- CORS is enabled by default on GitHub Pages for all origins (`*`), allowing web and mobile fetch.

## Published Endpoints

| Endpoint | Content | Size (est.) | Purpose |
|---|---|---|---|
| `/data/manifest.json` | Dataset metadata, sha256 hashes, versioning | ~4 KB | Stale-while-revalidate version check |
| `/data/categories.json` | Full list of 20 categories + subcategories | ~12 KB | Category browsing |
| `/data/tags.json` | Array of recognized tags | ~2 KB | Tag filtering |
| `/data/collections.json` | Curated editorial collections | ~4 KB | Curated showcases |
| `/data/tools/index.json` | Compact array of all published tools | ~40 KB | Directory view, search, offline cache |
| `/data/tools/<slug>.json`| Full detailed record for specific tool | ~2 KB | Detail screens / deep dive |
| `/data/search-index.json`| Pre-tokenized search documents | ~25 KB | Fast client-side search |

## Rollback Procedure
If a corrupted dataset or inaccurate pricing is accidentally deployed:
1. Revert the commit in Git: `git revert HEAD`.
2. Re-run `python scripts/validate.py && python scripts/build_indexes.py`.
3. Push to `main`.
4. Within 60 seconds, GitHub Actions redeploys the previous clean state to GitHub Pages.
