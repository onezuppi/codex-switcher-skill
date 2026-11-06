"""Account store and Codex auth.json helpers. Tokens are never printed."""
import datetime
import json
import os
import sys
import tempfile

TOKEN_KEYS = ("id_token", "access_token", "refresh_token")


def codex_home():
    return os.path.expanduser("~/.codex")


def switcher_dir():
    return os.path.expanduser("~/.codex-switcher")


def accounts_path():
    return os.path.join(switcher_dir(), "accounts.json")


def auth_path():
    return os.path.join(codex_home(), "auth.json")


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """Write atomically so a crash never leaves a half-written token file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def load_store():
    if not os.path.exists(accounts_path()):
        sys.exit(f"Account file not found: {accounts_path()}. Add accounts in Codex Switcher first.")
    return load_json(accounts_path())


def active_account(store):
    return next((a for a in store["accounts"] if a["id"] == store.get("active_account_id")), None)


def find_account(store, ref):
    """Resolve an account by 1-based index, id, email or name."""
    accounts = store["accounts"]
    if ref.isdigit() and 1 <= int(ref) <= len(accounts):
        return accounts[int(ref) - 1]
    matches = [a for a in accounts if ref in (a["id"], a.get("email"), a.get("name"))]
    if len(matches) != 1:
        sys.exit(f"Account '{ref}' not found or ambiguous. Run 'list' and use the index.")
    return matches[0]


def account_index(store, account):
    return store["accounts"].index(account) + 1


def sync_auth_file(acc):
    """Copy the active account's tokens into the Codex auth.json, keeping other keys."""
    auth = load_json(auth_path()) if os.path.exists(auth_path()) else {}
    tokens = auth.get("tokens", {})
    for key in TOKEN_KEYS:
        if key in acc["auth_data"]:
            tokens[key] = acc["auth_data"][key]
    tokens["account_id"] = acc["auth_data"]["account_id"]
    auth["tokens"] = tokens
    auth["last_refresh"] = now_iso()
    save_json(auth_path(), auth)


def write_back_active_tokens(store):
    """Codex refreshes tokens in auth.json itself. Keep the store in sync before a switch."""
    acc = active_account(store)
    if not acc or not os.path.exists(auth_path()):
        return
    tokens = load_json(auth_path()).get("tokens", {})
    if tokens.get("account_id") != acc["auth_data"].get("account_id"):
        return
    for key in TOKEN_KEYS:
        if key in tokens:
            acc["auth_data"][key] = tokens[key]
