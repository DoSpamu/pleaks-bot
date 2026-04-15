# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Automates activity on the Polish forum **pleaks.st** (XenForo 2.x) — logging in with TOTP 2FA, scraping threads, and posting replies/new threads with randomized timing to appear human.

Target forum sections (award points): Sztuczna Inteligencja, Pieniadze, Darmowe.

## Running the scripts

```bash
# First-time login — requires a live 6-digit TOTP code (valid ~60s)
python login_and_scrape.py <TOTP_CODE>

# Post automation — uses saved session (no TOTP needed until session expires)
python autopost.py
```

Session is saved to `session_cookies.json` (valid ~30 days, in `.gitignore`). If `autopost.py` prints `[!] Sesja wygasla!`, re-run `login_and_scrape.py` with a fresh TOTP.

## Architecture

Three scripts, each self-contained:

- **`login_and_scrape.py`** — logs in via `/login/` (not the nav button, which is hidden in off-canvas menu), handles the `/login/two-step` TOTP page, then crawls forum sections and saves thread links + cookies.
- **`autopost.py`** — the main bot. `POSTS` list at the top defines all replies and new threads. `gen_delays()` spreads them over ~40 minutes with random gaps (45–240s). `fill_editor()` handles XenForo's Froala editor via three JS fallbacks (hidden textarea → Froala `.fr-element` → contenteditable).
- **`scrape_threads.py`** — earlier exploration script, kept for reference.

## XenForo specifics

- Hash URLs like `#darmowe.93` are **category nodes**, not browsable forums. Actual forum URLs: `/forums/kryptowaluty.81/`, `/forums/aktualnoci-i-dyskusje.180/`, etc.
- The editor fill uses a native input setter trick — plain `.fill()` on the hidden textarea doesn't trigger XenForo's reactivity.
- New thread URL pattern: `https://pleaks.st/forums/{slug}.{id}/create-thread`
- Quick reply submit selector: `.js-quickReply button[type="submit"]`

## Adding new posts

Edit the `POSTS` list in `autopost.py`:

```python
# Reply to existing thread
{"type": "reply", "url": "https://pleaks.st/threads/slug.ID/", "content": "..."}

# Create new thread
{"type": "new_thread", "forum_url": "https://pleaks.st/forums/slug.ID/create-thread",
 "title": "...", "content": "..."}
```

Content style: natural Polish, no em-dashes (`—`), varied length, no overly formal structure.
