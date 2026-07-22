# Realistic AI Bot — revival draft README

**This is a draft, not the live README.** See "Collision note" immediately below before doing
anything with this file.

Generated 2026-07-11 as part of shortlist entry #13 ("Realistic AI Bot — revive-later (fun
flagship)"). Full evidence pack, built-vs-vision table, rot check, and a not-yet-executed demo
plan live at
`/Users/petrlavrov/work/prototypes/agent-coordination/reports/builds/realistic-ai-bot-revival.md`.

---

## Collision note

This repo already has a `README.md`. It is the unmodified generic `botspot-template` boilerplate
(the template this repo was scaffolded from, per `pyproject.toml`'s `[template]` block:
`url = "https://github.com/calmmage/botspot-template.git"`, `version = "0.3.2"`). It documents a
`app/` directory layout (`app/_app.py`, `app/bot.py`, `app/router.py`) that does not exist in this
repo — the real code lives under `src/` (`src/app.py`, `src/bot.py`, `src/router.py`,
`src/routers/settings.py`). That mismatch is concrete evidence the template README was never
updated after the project diverged from the template.

Per the task that produced this draft, `README.md` was **not overwritten** (a README.md already
existed, so the "only if no README.md exists" condition did not hold). This file is a sibling
draft. To adopt it, a human replaces `README.md`'s content with this file's content — that
replacement was deliberately not done here.

---

## What this is

Petr's own framing, in order of appearance:

- Telegram, 2025-05-08 (2 days before the repo existed): *"Тестирую простую идею - Realistic AI
  chatbot / Чтобы отвечал тебе по кусочкам, а не спамил сразу миллион сообщений"* — "Testing a
  simple idea - Realistic AI chatbot. So it answers you in pieces, instead of spamming a million
  messages at you all at once."
- `dev/0_idea.md` (the repo's own founding note): *"Ok, so what's the idea? Simple: I want to make
  a realistic AI chatbot. What does it mean? Well, at least - send separate messages! Add delays?"*
- `src/router.py`'s own shipped `/start` text: *"This is Realistic AI Bot. An experimental project
  to make chatting with AI to feel like chatting with a real human."*

## The core experience (Petr's vision, verbatim)

From the canonical vision note, `/Users/petrlavrov/work/mainline/obsidian/ws-11-jun/fun/Realistic
AI bot.md` (frontmatter `type: vision`; captured via Telegram 2026-06-11, written up as this note
2026-06-13):

> Realistic AI bot
> - writing style like a human
> - responds with SEPARATE messages, with time delay, "typing"/thinks between them
> - starts conversation randomly
>
> Personality
> - Has character / preferences
> - list of topics of interest. Can accept / reject topics to the interest set (rarely) or
>   randomly acquire / drop them (on encountering elsewhere)
> - when starting conversations randomly, uses preferred topics set  as guidance for selection of
>   what to say.

That's the whole vision — five bullets, nothing more implied. The shortlist entry (`reports/
shortlist.md` #13 in the agent-coordination repo) rates it "clear/medium (core experience vs misc
ops)" — meaning the bullets above are clear, but plenty of *other* things got built in this repo
that were never part of this vision (model picker, splitter-mode variants, etc. — see the
built-vs-vision table in the revival pack).

## What was actually built

Full git log (17 commits, all real, shown in the revival pack's Verification section). The
headline arc:

| When | Commit | Message |
|---|---|---|
| 2025-05-10 15:38 +03:00 | `66a4a39` | Initial commit *(author: "Reliable Magician" — the botspot-template scaffold bot, not Petr)* |
| 2025-05-10 16:41–17:32 +03:00 | `c9f1ac4`, `cdd37ae`, `cae976c` | Initialization — copy over existing files / dev notes |
| 2025-05-11 02:20 +03:00 | `e8a6373` | **v0.1.0 - realistic ai chatbot, first version!** |
| 2025-05-11 05:03 +03:00 | `c388f84` | **Chat coordinator prototype - works!** |
| 2025-05-11 05:06 +03:00 | `09c67aa` | Chat coordinator prototype - event timeline |
| 2025-05-11 17:16 +03:00 | `d0bea59` | v0.1.3 - add a proper start message |
| 2025-05-12 02:22 +03:00 | `28f0767` | v0.1.4 - Update start message |
| 2025-05-12 03:12 +03:00 | `90f650d` | **Add tests** |
| 2025-08-27 05:44 +03:00 | `f6fee7e` | Add llm files to gitignore and rename CLAUDE.md to LLM_RULES.md *(last commit; administrative only)* |

The entire feature build — initial commit through "Add tests" — happened inside **1 day 11.5
hours** (2025-05-10 15:38 to 2025-05-12 03:12). One lone housekeeping commit followed 107 days
later; nothing since.

What shipped and is live in `src/` today:

- **Message splitting** — `App.split_message()` in `src/app.py`, `SplitterMode.SIMPLE_IMPROVED`
  active by default (splits on `\n\n`, re-merges short fragments below
  `splitter_min_message_length=200` chars).
- **Delay + typing status between messages** — `App.send_messages()`, `DelayMode.RANDOM` active by
  default (`delay_random_min=0.0`, `delay_random_max=10.0`), wraps botspot's `typing_status()`
  around each `asyncio.sleep()`.
- **Model picker** — `/set_model`, 12 models across Anthropic/OpenAI/Google/xAI via litellm.
- **Tests** — 5 files, 34 test functions total (`test_app.py` 17, `test_settings.py` 8,
  `test_router.py` 5, `test_bot.py` 3, `test_imports.py` 1), added in the single `90f650d` "Add
  tests" commit.
- A photographed whiteboard sketch, `dev/chat_coordinator/event_timeline.png` (the "event
  timeline" commit) — Petr's own hand-drawn diagram: input message -> buffer -> start processing
  -> send response, with a "receive response / new input" branch. Genuine design artifact, not an
  AI-generated one.

What's in `dev/` but was **never wired into `src/`**: three successive sketches of a
"ChatCoordinator" (`dev/chat_coordinator.py`, `dev/chat_coordinator_claude.py`,
`dev/chat_coordinator/chat_coordinator_prototype.py` + `.ipynb`), meant to carry
accumulation/offline-mode/random-activation/interruption. `src/app.py` still has the import
commented out: `# from dev.chat_coordinator_claude import ChatCoordinator`. See the revival pack's
built-vs-vision table for exactly which vision pieces that gap accounts for.

## Architecture as found

```
realistic-ai-bot/
├── run.py                       # entrypoint: load_dotenv(.env), calls src.bot.main()
├── src/
│   ├── app.py                   # App: config (pydantic-settings), split_message(), send_messages()
│   ├── bot.py                   # aiogram Bot + Dispatcher, botspot BotManager, dp.run_polling()
│   ├── router.py                # /start, /help, catch-all chat_handler (generate -> split -> send)
│   └── routers/
│       └── settings.py          # /set_model, /set_splitter_mode (hidden), /set_delay_mode (hidden)
├── tests/                       # 5 files, 34 test functions
├── dev/                         # design notes + 3 unshipped ChatCoordinator prototypes
│   ├── 0_idea.md                       # the founding idea (quoted above)
│   ├── 1_plan.md                       # deploy / history / streaming / parallel / "write me randomly"
│   ├── 2_chat_coordinator_rework.md    # event-flow sketch (activation types, self-activation flow)
│   ├── todo.md                         # fullest first-hand feature checklist, done vs open
│   ├── chat_coordinator.py             # sketch #1 (apscheduler, stub handlers, unfinished)
│   ├── chat_coordinator_claude.py      # sketch #2, fullest — per-user queues + activation events
│   ├── chat_coordinator/
│   │   ├── chat_coordinator_prototype.py / .ipynb   # sketch #3 + a local (non-Telegram) console
│   │   │                                              chat-loop emulator (`while True: input()`)
│   │   └── event_timeline.png          # whiteboard photo, see above
│   └── dev.ipynb                       # unrelated markdown->HTML formatting scratch (mistune)
├── botspot_101.md               # botspot framework cheatsheet (docs, not app code)
├── pyproject.toml                # realistic-ai-bot 0.1.4, python >=3.12,<4.0
├── example.env                   # no .env committed (correct — would hold real secrets)
├── Dockerfile / docker-compose.yaml
├── .github/workflows/main.yml    # CI: poetry install + pytest on push, py3.12 & 3.13
├── .github/workflows/release.yml # tag-triggered release workflow (no tags exist in this repo)
└── README.md                     # existing generic template README (unchanged, see collision note)
```

No `poetry.lock` (or any lockfile) is committed anywhere in this repo — dependency versions were
never pinned. `botspot` and `calmlib` are both `git = ... branch = "main"` dependencies in
`pyproject.toml`, i.e. floating. See the revival pack's rot check for why that matters.

## Status

**Stale, not actively broken-by-code — dormant.** 318 days (about 10.4 months; the shortlist's
"~11 months" is the same gap, rounded) between the last commit (2025-08-27) and today
(2026-07-11). Nothing in the code changed in that window; what may have changed underneath it
(botspot/calmlib upstream, LLM provider model catalogs) is unverified — see the rot check in the
revival pack, which also surfaces telegram-corpus evidence that the deployed bot has been silently
erroring on every incoming message since at least 2025-09-18.

One concrete, verified-by-reading bug, unrelated to dependency drift: the `/help` handler in
`src/router.py` builds its message from a plain `"""..."""` string, not an f-string (the file's
only `f"""` is in `start_handler`) — so `/help` would literally send the text `This is
{app.name}!` with the braces intact instead of interpolating "Realistic AI Bot".

## Revival path

This README is the "safe half" of the revival: evidence + documentation, no code run, no bot
deployed, no message sent. The other half — the full verbatim-quote vision pack, a built-vs-vision
table, the rot check, a bounded (not-executed) demo plan, three labeled character-concept
suggestions, and open questions for Petr — is at:

`/Users/petrlavrov/work/prototypes/agent-coordination/reports/builds/realistic-ai-bot-revival.md`
