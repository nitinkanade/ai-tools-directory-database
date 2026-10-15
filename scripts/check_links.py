#!/usr/bin/env python3
"""
Automated Dead-Link and URL Health Checker for AI Tools Directory.
Verifies that all external website URLs and repository URLs are live,
resolving HTTP 200/301/302 codes and detecting dead/broken links.
"""

import argparse
import concurrent.futures
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

DATABASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(DATABASE_DIR, "data", "tools")

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Custom redirect handler to record intermediate redirect status codes
class RedirectTracker(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.redirects = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects.append((code, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def check_single_url(url, timeout=10):
    """
    Checks an individual URL for health.
    Attempts HEAD request first; falls back to GET if HEAD is rejected.
    Returns a dict with status_code, category, final_url, error, elapsed_ms.
    """
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return {
            "url": url,
            "status_code": 0,
            "category": "INVALID_URL",
            "error": "URL missing or lacks http/https scheme",
            "elapsed_ms": 0,
            "final_url": url,
        }

    start_time = time.time()
    headers = {
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # SSL context that tolerates modern server certificates
    ctx = ssl.create_default_context()

    def do_request(method):
        tracker = RedirectTracker()
        opener = urllib.request.build_opener(tracker, urllib.request.HTTPSHandler(context=ctx))
        req = urllib.request.Request(url, headers=headers, method=method)
        with opener.open(req, timeout=timeout) as response:
            return response.getcode(), response.geturl(), tracker.redirects

    # Attempt 1: HEAD
    try:
        code, final_url, redirects = do_request("HEAD")
        elapsed = int((time.time() - start_time) * 1000)
        return {
            "url": url,
            "status_code": code,
            "category": "LIVE",
            "final_url": final_url,
            "redirects": redirects,
            "error": None,
            "elapsed_ms": elapsed,
        }
    except urllib.error.HTTPError as e:
        # Some servers reject HEAD with 405 Method Not Allowed or 403 Forbidden
        if e.code in (403, 405, 501):
            try:
                # Fallback to GET
                code, final_url, redirects = do_request("GET")
                elapsed = int((time.time() - start_time) * 1000)
                return {
                    "url": url,
                    "status_code": code,
                    "category": "LIVE",
                    "final_url": final_url,
                    "redirects": redirects,
                    "error": None,
                    "elapsed_ms": elapsed,
                }
            except urllib.error.HTTPError as ge:
                elapsed = int((time.time() - start_time) * 1000)
                # Cloudflare or DDOS guard bot challenges return 403
                category = "BOT_CHALLENGE" if ge.code in (403, 429) else "DEAD"
                return {
                    "url": url,
                    "status_code": ge.code,
                    "category": category,
                    "final_url": url,
                    "redirects": [],
                    "error": f"HTTP {ge.code}: {ge.reason}",
                    "elapsed_ms": elapsed,
                }
            except Exception as ge:
                elapsed = int((time.time() - start_time) * 1000)
                return {
                    "url": url,
                    "status_code": 0,
                    "category": "DEAD",
                    "final_url": url,
                    "redirects": [],
                    "error": str(ge),
                    "elapsed_ms": elapsed,
                }
        else:
            elapsed = int((time.time() - start_time) * 1000)
            return {
                "url": url,
                "status_code": e.code,
                "category": "DEAD" if e.code in (404, 410, 500, 502, 503) else "ERROR",
                "final_url": url,
                "redirects": [],
                "error": f"HTTP {e.code}: {e.reason}",
                "elapsed_ms": elapsed,
            }
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        return {
            "url": url,
            "status_code": 0,
            "category": "DEAD",
            "final_url": url,
            "redirects": [],
            "error": str(e),
            "elapsed_ms": elapsed,
        }

def collect_tools_from_dir(tools_dir):
    """Loads all tool JSON files from the directory."""
    tools = []
    if not os.path.exists(tools_dir):
        return tools

    for fname in sorted(os.listdir(tools_dir)):
        if fname.endswith(".json"):
            fp = os.path.join(tools_dir, fname)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tools.append(data)
            except Exception as e:
                print(f"[WARN] Failed reading {fname}: {e}")
    return tools

def check_all_tools(tools, timeout=10, max_workers=8):
    """Checks all tool URLs concurrently."""
    tasks = []
    for t in tools:
        tool_id = t.get("id") or t.get("slug")
        tool_name = t.get("name", tool_id)
        web_url = t.get("websiteUrl")
        if web_url:
            tasks.append({"tool_id": tool_id, "tool_name": tool_name, "type": "website", "url": web_url})
        src_url = t.get("sourceCodeUrl")
        if src_url:
            tasks.append({"tool_id": tool_id, "tool_name": tool_name, "type": "source", "url": src_url})

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(check_single_url, item["url"], timeout): item
            for item in tasks
        }
        for future in concurrent.futures.as_completed(future_map):
            meta = future_map[future]
            try:
                res = future.result()
            except Exception as exc:
                res = {
                    "url": meta["url"],
                    "status_code": 0,
                    "category": "DEAD",
                    "error": str(exc),
                    "elapsed_ms": 0,
                }
            merged = {**meta, **res}
            results.append(merged)

    # Sort results deterministically by tool_id and type
    results.sort(key=lambda r: (r["tool_id"], r["type"]))
    return results

def generate_markdown_report(results, generated_at=None):
    """Builds a formatted Markdown health report."""
    if generated_at is None:
        generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    total = len(results)
    live = sum(1 for r in results if r["category"] in ("LIVE", "BOT_CHALLENGE"))
    dead = sum(1 for r in results if r["category"] == "DEAD")
    bot_protected = sum(1 for r in results if r["category"] == "BOT_CHALLENGE")

    lines = [
        "# AI Tools Directory — URL Health & Dead-Link Report",
        "",
        f"- **Generated At**: `{generated_at}`",
        f"- **Total URLs Checked**: `{total}`",
        f"- **Live & Accessible**: `{live}` (including {bot_protected} bot-protected)",
        f"- **Dead / Broken Links**: `{dead}`",
        "",
        "## Summary by Status",
        "",
        "| Category | Count | Status |",
        "| :--- | :--- | :--- |",
        f"| Live (200-399) | {sum(1 for r in results if r['category'] == 'LIVE')} | [OK] |",
        f"| Bot Guarded (403/429) | {bot_protected} | [OK - Live Host] |",
        f"| Dead / Broken | {dead} | {'[ACTION REQUIRED]' if dead > 0 else '[NONE]'} |",
        "",
        "## Detailed Link Audit",
        "",
        "| Tool | Type | URL | Status | Result | Response Time |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        status_disp = str(r.get("status_code", "-"))
        cat = r.get("category", "UNKNOWN")
        icon = "[OK]" if cat in ("LIVE", "BOT_CHALLENGE") else "[DEAD]"
        elapsed = f"{r.get('elapsed_ms', 0)}ms"
        lines.append(
            f"| **{r['tool_name']}** | {r['type']} | [{r['url']}]({r['url']}) | {status_disp} | {icon} {cat} | {elapsed} |"
        )

    if dead > 0:
        lines.extend([
            "",
            "## Broken Links Requiring Immediate Attention",
            "",
        ])
        for r in results:
            if r["category"] == "DEAD":
                lines.append(f"- **{r['tool_name']}** ({r['type']}): `{r['url']}` &rarr; *{r.get('error')}*")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Check external URLs in AI Tools dataset.")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds (default: 10)")
    parser.add_argument("--workers", type=int, default=8, help="Concurrency workers (default: 8)")
    parser.add_argument("--fail-on-dead", action="store_true", help="Exit code 1 if dead links are found")
    parser.add_argument("--output", type=str, default="", help="File path to save Markdown report")
    args = parser.parse_args()

    print(f"--> Scanning tools in {TOOLS_DIR}...")
    tools = collect_tools_from_dir(TOOLS_DIR)
    print(f"--> Loaded {len(tools)} tools. Checking links concurrently (workers={args.workers}, timeout={args.timeout}s)...")

    results = check_all_tools(tools, timeout=args.timeout, max_workers=args.workers)

    dead_count = sum(1 for r in results if r["category"] == "DEAD")
    live_count = sum(1 for r in results if r["category"] in ("LIVE", "BOT_CHALLENGE"))
    print(f"\n[AUDIT COMPLETE] Checked {len(results)} URLs: {live_count} Live, {dead_count} Dead.")

    report_md = generate_markdown_report(results)

    # Output to specified file
    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"--> Saved report to {out_path}")

    # Output to GitHub Step Summary if running in Actions
    gh_step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if gh_step_summary:
        try:
            with open(gh_step_summary, "a", encoding="utf-8") as f:
                f.write("\n\n" + report_md + "\n")
            print("--> Appended report to GITHUB_STEP_SUMMARY.")
        except Exception as e:
            print(f"[WARN] Failed writing to GITHUB_STEP_SUMMARY: {e}")

    if dead_count > 0 and args.fail_on_dead:
        print(f"[FAIL] Found {dead_count} dead link(s)!")
        sys.exit(1)

    print("[SUCCESS] Link check finished cleanly.")

if __name__ == "__main__":
    main()
