# codex-accounts-skill

An agent skill that lets Claude Code, Codex, or any agent that supports
`SKILL.md` skills manage multiple Codex (ChatGPT) accounts from chat:

- list saved accounts
- check the 5-hour and weekly usage limits of each account
- find the account with the most room
- switch the active Codex login

It is a companion to [Codex Switcher](https://github.com/Lampese/codex-switcher)
by [Lampese](https://github.com/Lampese). The skill reads the account list that
Codex Switcher keeps in `~/.codex-switcher/accounts.json`, so you add and remove
accounts in that app. This project is unofficial and is not affiliated with
Codex Switcher, OpenAI, or Anthropic.

## Requirements

- Python 3.7+ (standard library only, no packages to install)
- [Codex Switcher](https://github.com/Lampese/codex-switcher) with at least one
  ChatGPT account added
- Network access to `chatgpt.com` and `auth.openai.com`
- Windows for automatic close and reopen of Codex. On macOS and Linux the
  commands work, but you close and reopen Codex yourself. Only Windows is tested.

## Install

Copy the skill folder into your agent's skills directory.

```bash
git clone https://github.com/onezuppi/codex-accounts-skill.git
# Claude Code
cp -r codex-accounts-skill/skills/codex-accounts ~/.claude/skills/
# Codex
cp -r codex-accounts-skill/skills/codex-accounts ~/.codex/skills/
```

On Windows PowerShell use `Copy-Item -Recurse` with the same paths.

## Usage

Ask your agent in plain language:

- "Which Codex account has the most limit left?"
- "Switch Codex to account 2."
- "Show my Codex limits."

Or run the script directly:

```bash
python skills/codex-accounts/scripts/codex_accounts.py list
python skills/codex-accounts/scripts/codex_accounts.py limits --all
python skills/codex-accounts/scripts/codex_accounts.py switch 2 --dry-run
python skills/codex-accounts/scripts/codex_accounts.py switch 2
```

`switch` closes Codex and Codex Switcher, writes the new login to
`~/.codex/auth.json`, and reopens Codex. Add `--no-reopen` to keep it closed.
Unsaved work in Codex is lost, so save first.

## Safety

- The script never prints tokens. It reads them only inside its own process.
- Before each switch it backs up `~/.codex/auth.json` to
  `~/.codex-switcher/backups/` with mode 600. To roll back, copy the newest
  backup over `~/.codex/auth.json`.
- `limits` calls an **undocumented** ChatGPT endpoint (`/backend-api/wham/usage`)
  and may refresh your OAuth tokens. The endpoint can change or break at any
  time.
- Use this only with accounts you own. Do not use it for account sharing or
  pooling, or to bypass OpenAI's terms. You are responsible for how you use it.
- The skill touches your credentials. Read `scripts/` before you install it.

## Layout

```
skills/codex-accounts/
  SKILL.md              instructions for the agent
  scripts/
    codex_accounts.py   CLI entry point
    store.py            account store and auth.json helpers
    usage.py            usage limits and token refresh
    apps.py             close and reopen Codex (Windows)
```

## License

[MIT](LICENSE)
