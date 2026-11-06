---
name: codex-accounts
description: List Codex (ChatGPT) accounts saved by Codex Switcher, check remaining 5-hour and weekly usage limits, find the account with the most room, and switch the active Codex login. Use when the user asks to switch Codex account, check Codex limits or quota, or pick a free account. Trigger phrases - "switch codex account", "codex limits", "which account has room", "codex-switcher". Reads only account metadata and usage numbers, never prints tokens.
license: MIT
compatibility: Python 3.7+ (standard library only). Needs network access to chatgpt.com and auth.openai.com, and Codex Switcher (github.com/Lampese/codex-switcher) accounts in ~/.codex-switcher/accounts.json. Automatic close and reopen of Codex works on Windows only.
---

# Codex accounts

Runs `scripts/codex_accounts.py` to do what Codex Switcher does: list saved
accounts, show usage limits, and switch the Codex login.

## Hard rules

- **Never print, quote, or summarize token values.** `accounts.json` and
  `auth.json` hold `access_token`, `refresh_token` and `id_token`. Do not
  `cat`, read, or print these files. Use the script. If you must inspect a
  file, print key names only.
- **Ask before switching.** `switch` changes which login Codex uses. Run it only
  when the user asks to switch, or after they confirm the account you picked.
- **Warn before `switch`.** It closes Codex and Codex Switcher, force-kills what
  is still running after 15 seconds, then reopens Codex. Unsaved Codex work is
  lost. Pass `--no-reopen` to leave Codex closed.
- **Close or confirm Codex Switcher.** The GUI writes the same `accounts.json`.
  `switch` closes it on Windows. On other systems ask the user to close it.

## Commands

Run from any directory. Use `python3` if `python` is not on PATH:

```bash
python "<skill-dir>/scripts/codex_accounts.py" <command>
```

| Command | What it does |
|---|---|
| `list` | Accounts table: index, name, email, plan, subscription end date. `*` marks the active one. |
| `current` | Name and email of the active account. |
| `limits` | Usage for the active account. |
| `limits --all` | Usage for every account. Use it to compare accounts. |
| `limits 2 work` | Usage for chosen accounts, by index, id, email or name. |
| `switch 2 --dry-run` | Show what a switch would do. Writes nothing. Run it first. |
| `switch 2` | Switch the login, then reopen Codex. |
| `switch 2 --no-reopen` | Switch the login and leave Codex closed. |

`limits` prints the 5-hour and weekly windows (percent used, reset time) and the
credit balance when the account has credits.

## Typical flows

**"Which account has room?"** Run `limits --all`. Report percent used and reset
time per account in a short table. Name the account with the most room. Do not
switch unless asked.

**"Switch to another account."** Run `list`, then `switch N --dry-run`. Ask for
confirmation, then run `switch N`.

**"Switch to the one with room."** Run `limits --all`, pick the lowest usage,
and confirm the choice with the user before `switch`.

## Notes

- Before each switch the script backs up `~/.codex/auth.json` to
  `~/.codex-switcher/backups/` (mode 600). Rollback: copy the newest backup over
  `~/.codex/auth.json`.
- Before each switch the script copies tokens that Codex refreshed in
  `auth.json` back into `accounts.json`.
- When an access token expires, `limits` refreshes it and saves the new token.
  This is normal.
- HTTP 403 from the usage endpoint is usually a temporary Cloudflare block. Retry
  later. Do not retry in a loop.
- The usage endpoint is undocumented. If the script reports "unrecognized
  response shape", show the printed field names to the user. The script may need
  an update.
- Only ChatGPT accounts (`auth_mode` = `chat_g_p_t`) can be switched or checked.
  API-key accounts are skipped.
