#!/usr/bin/env python3
"""Manage Codex accounts the way Codex Switcher does.

Commands:
  list                      show saved accounts (no tokens)
  current                   show the active account
  limits [ACCOUNT ...]      show rate-limit usage (--all for every account)
  switch ACCOUNT            make ACCOUNT the active Codex login

Tokens are read only inside this process. They are never printed.
ACCOUNT is an index from `list`, an id, an email, or a name.
"""
import argparse
import datetime
import os
import shutil
import sys

from apps import close_apps, open_codex
from store import (TOKEN_KEYS, account_index, accounts_path, active_account, auth_path, find_account,
                   load_json, load_store, now_iso, save_json, switcher_dir, write_back_active_tokens)
from usage import fetch_usage, print_usage


def label(store, acc):
    return f"[{account_index(store, acc)}] {acc.get('name')} <{acc.get('email')}>"


def cmd_list(_args):
    store = load_store()
    active_id = store.get("active_account_id")
    print(f"{'#':>2}  {'*':1}  {'name':20} {'email':32} {'plan':10} {'subscription until':20}")
    for i, a in enumerate(store["accounts"], 1):
        mark = "*" if a["id"] == active_id else ""
        until = (a.get("subscription_expires_at") or "-")[:10]
        print(f"{i:>2}  {mark:1}  {a.get('name', '-')[:20]:20} {a.get('email', '-')[:32]:32} "
              f"{a.get('plan_type', '-')[:10]:10} {until:20}")


def cmd_current(_args):
    store = load_store()
    acc = active_account(store)
    print(f"Active: {label(store, acc)}" if acc else "No active account is set.")


def cmd_limits(args):
    store = load_store()
    if args.all:
        targets = store["accounts"]
    elif args.accounts:
        targets = [find_account(store, ref) for ref in args.accounts]
    else:
        active = active_account(store)
        if not active:
            sys.exit("Specify an account or use --all.")
        targets = [active]
    for acc in targets:
        print(f"{label(store, acc)} ({acc.get('plan_type')})")
        if acc.get("auth_mode") != "chat_g_p_t":
            print("  usage limits exist only for ChatGPT accounts; this account has another type")
            continue
        print_usage(fetch_usage(store, acc))


def backup_auth_file():
    """Copy the current auth.json to ~/.codex-switcher/backups/ with mode 600."""
    if not os.path.exists(auth_path()):
        return
    backup_dir = os.path.join(switcher_dir(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup = os.path.join(backup_dir, f"auth-{datetime.datetime.now():%Y%m%d-%H%M%S}.json")
    shutil.copy2(auth_path(), backup)
    os.chmod(backup, 0o600)


def cmd_switch(args):
    store = load_store()
    target = find_account(store, args.account)
    if target.get("auth_mode") != "chat_g_p_t":
        sys.exit("Switching is supported only for ChatGPT accounts.")
    if store.get("active_account_id") == target["id"]:
        print(f"{label(store, target)} is already active.")
        return
    if args.dry_run:
        print(f"Dry run: would switch to {label(store, target)}. No files changed.")
        return

    # Codex must be closed before its login changes. Closing it first lets it write any
    # refreshed tokens to auth.json, so reload the store after the close and sync them.
    close_apps()
    store = load_store()
    target = find_account(store, args.account)
    write_back_active_tokens(store)
    backup_auth_file()

    auth = load_json(auth_path()) if os.path.exists(auth_path()) else {}
    auth["OPENAI_API_KEY"] = None
    auth["tokens"] = {k: target["auth_data"][k] for k in (*TOKEN_KEYS, "account_id")}
    auth["last_refresh"] = now_iso()
    save_json(auth_path(), auth)

    target["last_used_at"] = now_iso()
    store["active_account_id"] = target["id"]
    save_json(accounts_path(), store)
    print(f"Active account: {label(store, target)}")

    if args.no_reopen:
        print("Codex was not reopened. Open it manually.")
    else:
        open_codex()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show saved accounts").set_defaults(func=cmd_list)
    sub.add_parser("current", help="show active account").set_defaults(func=cmd_current)

    p_limits = sub.add_parser("limits", help="show rate-limit usage")
    p_limits.add_argument("accounts", nargs="*", help="account index, id, email or name")
    p_limits.add_argument("--all", action="store_true", help="every account")
    p_limits.set_defaults(func=cmd_limits)

    p_switch = sub.add_parser("switch", help="make an account active (closes and reopens Codex)")
    p_switch.add_argument("account", help="account index, id, email or name")
    p_switch.add_argument("--dry-run", action="store_true", help="show the change, write nothing")
    p_switch.add_argument("--no-reopen", action="store_true", help="do not open Codex after the switch")
    p_switch.set_defaults(func=cmd_switch)
    return parser


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
