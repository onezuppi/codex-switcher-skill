"""Usage limits and token refresh. Talks to chatgpt.com and auth.openai.com."""
import datetime
import json
import sys
import urllib.error
import urllib.request

from store import TOKEN_KEYS, accounts_path, save_json, sync_auth_file

# Public OAuth client id of the official Codex CLI. It is not a secret.
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
# Undocumented endpoint used by the Codex apps. It can change without notice.
USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
TOKEN_URL = "https://auth.openai.com/oauth/token"

FIVE_HOURS = 18000
ONE_WEEK = 604800


def refresh_tokens(store, acc):
    body = json.dumps({
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": acc["auth_data"]["refresh_token"],
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            fresh = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"Could not refresh the account tokens (HTTP {e.code}). Sign in to the account again.")
    for key in TOKEN_KEYS:
        if key in fresh:
            acc["auth_data"][key] = fresh[key]
    save_json(accounts_path(), store)
    if store.get("active_account_id") == acc["id"]:
        sync_auth_file(acc)


def fetch_usage(store, acc):
    """Return the usage JSON, or {"_error": message}. Refreshes expired tokens once."""
    def request():
        headers = {
            "Authorization": f"Bearer {acc['auth_data']['access_token']}",
            "ChatGPT-Account-Id": acc["auth_data"]["account_id"],
            "User-Agent": "codex-cli",
        }
        with urllib.request.urlopen(urllib.request.Request(USAGE_URL, headers=headers), timeout=30) as resp:
            return json.load(resp)

    try:
        return request()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            refresh_tokens(store, acc)
            try:
                return request()
            except urllib.error.HTTPError as e2:
                return {"_error": f"HTTP {e2.code} after token refresh"}
        if e.code == 403:
            return {"_error": "HTTP 403 (possibly a temporary Cloudflare block, retry later)"}
        return {"_error": f"HTTP {e.code}"}


def format_reset(window):
    if window.get("reset_at"):
        return datetime.datetime.fromtimestamp(window["reset_at"]).strftime("%Y-%m-%d %H:%M")
    if window.get("reset_after_seconds") is not None:
        return f"in {window['reset_after_seconds'] / 3600:.1f} h"
    return "-"


def window_label(window):
    seconds = window.get("limit_window_seconds")
    if seconds == FIVE_HOURS:
        return "5-hour"
    if seconds == ONE_WEEK:
        return "weekly"
    if seconds:
        return f"{seconds // 3600}-hour"
    return "window"


def print_usage(data):
    if "_error" in data:
        print(f"  error: {data['_error']}")
        return
    rate_limit = data.get("rate_limit") or {}
    found = False
    for key in ("primary_window", "secondary_window"):
        window = rate_limit.get(key) or data.get(key)
        if window:
            found = True
            print(f"  {window_label(window)}: {window.get('used_percent', '?')}% used, "
                  f"resets {format_reset(window)}")
    credits = data.get("credits")
    if credits:
        found = True
        balance = credits.get("balance")
        print(f"  credits: balance {'-' if balance is None else balance}, "
              f"unlimited {credits.get('unlimited', '?')}")
    if not found:
        print(f"  unrecognized response shape, top-level fields: {sorted(data.keys())}")
