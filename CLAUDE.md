# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Automates activity on the Polish forum **pleaks.st** (XenForo 2.x) — logging in with TOTP 2FA and posting replies/new threads with randomized timing to appear human.

Target forum sections (award points): Sztuczna Inteligencja, Pieniadze, Darmowe.

## Running the scripts

```bash
# First-time login — requires a live 6-digit TOTP code (valid ~60s)
python login_and_scrape.py <TOTP_CODE>

# Post automation — uses saved session, logs to autopost_log.txt
python autopost.py > autopost_log.txt 2>&1 &

# Retry failed new threads only
python post_new_threads.py
```

Session is saved to `session_cookies.json` (valid ~30 days, in `.gitignore`). If `[!] Sesja wygasla!` appears, re-run `login_and_scrape.py` with a fresh TOTP.

To kill the bot: `cmd //c "taskkill /F /PID <windows_pid>"` — use Windows PID from Task Manager, not the bash PID (they differ on Windows/Git Bash).

## Architecture

- **`login_and_scrape.py`** — logs in via `/login/` (not the nav button, hidden in off-canvas menu), handles `/login/two-step` TOTP page, saves cookies.
- **`autopost.py`** — main bot. `POSTS` list defines replies and new threads. `gen_delays()` spreads posts over ~40 minutes (45–240s gaps). `type_into_editor()` uses `keyboard.type()` — plain `.fill()` doesn't work with XenForo's Froala. `click_submit()` uses locator API not query_selector.
- **`post_new_threads.py`** — standalone script to retry failed new thread creation.
- **`scrape_threads.py`** — early exploration script, kept for reference.

## XenForo specifics

- Hash URLs like `#darmowe.93` are **category nodes**, not forum URLs. Real URLs: `/forums/kryptowaluty.81/`, `/forums/aktualnoci-i-dyskusje.180/`, etc.
- New thread form: XenForo uses `textarea[name="title"]`, **not** `input[name="title"]`.
- New thread URL redirects: `/create-thread` → `/post-thread` automatically.
- Editor fill: click `.fr-element` → `Ctrl+A` → `Delete` → `keyboard.type()`. JS innerHTML injection doesn't sync with React state.
- Submit: `page.locator("button", has_text="Odpowiedz").last.click()` — not CSS selector syntax.
- If Froala editor missing: scroll down, look for reply button to expand quick-reply box.
- Login: go directly to `https://pleaks.st/login/`, not the navbar button.

## Content style — CRITICAL

The account was banned once for AI-detectable content. Follow these rules strictly:

- **No period at end of posts** — the single biggest AI tell
- **Lowercase at sentence starts** — forum style
- **Short, fragmented sentences** — not essay structure
- **No AI words**: kluczowy, istotny, warto, należy, pozwala, umożliwia, zapewnia
- **No AI openers**: "w erze sztucznej inteligencji...", "w dzisiejszych czasach..."
- **No em-dashes** (`—`)
- **No structured paragraphs** — "Z jednej strony... Z drugiej..." is an AI pattern
- **Darmowe section**: 1–2 sentences max (natural for thank-you posts)
- **SI/Pieniadze**: 3–4 sentences, stream-of-consciousness, personal anecdotes

Polish forum style: `"ze"` not `"że"`, `"bo"` not `"ponieważ"`, informal abbreviations OK.

## Humanizer integration

`humanize_text()` in `autopost.py` integrates with `ai-text-humanizer.com` (free, no login, min 300 chars). Currently **disabled** (commented out in `post_reply()` and `create_thread()`). Enable only on explicit request — output tends to be overly formal Polish which looks more AI-like than the manually written style.

## Adding new posts

Edit the `POSTS` list in `autopost.py`. Remove already-replied threads (check memory for list of URLs already used by the account).

```python
{"type": "reply", "url": "https://pleaks.st/threads/slug.ID/", "content": "..."}
{"type": "new_thread", "forum_url": "https://pleaks.st/forums/slug.ID/post-thread",
 "title": "...", "content": "..."}
```
