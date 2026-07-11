# Realistic AI Bot

A chat experiment about making an AI feel less like a response box and more like a person on the
other side. The original Telegram bot already split long answers and paused between them. This
revival adds a local, playable slice of Petr's fuller vision: **timing, taste, changing interests,
and initiative**.

## Play it now

No bot token, API key, package install, or internet connection is needed:

```bash
cd /Users/petrlavrov/work/projects/realistic-ai-bot
python3 -m demo.server
```

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173).

The two-minute path through the demo:

1. Click **baby keyboard + game** (or write your own message).
2. Watch Mira think and answer in separate, timed bubbles.
3. See which topics entered her interest set in **what stuck**.
4. Click **skip ahead until she texts**. Her unsolicited message is chosen from those interests.
5. Offer her a topic. She can accept or refuse it instead of becoming interested in everything.

The browser UI and behavior engine are dependency-free. They run entirely on localhost and do not
send your text anywhere. The replies are a deliberately small local choreography engine, not a
claim that a ruleset replaces an LLM; it makes the distinctive interaction testable before paying
the integration cost.

For a fast automated/browser run, add `?pace=fast` to the URL. Normal pace preserves the visible
typing and thinking rhythm.

## Vision represented by the slice

The canonical vision note says the bot should:

- write like a human;
- respond in separate messages with delays and visible thinking;
- start conversations randomly;
- have character and preferences;
- acquire, reject, and drop interests, then use them to decide what to bring up.

The demo implements each as an inspectable interaction. Mira is one concrete character concept,
not a claim that her exact personality was specified in the source note.

## Test the slice

```bash
python3 -m unittest tests.test_demo -v
```

The focused suite covers character state, paced multi-message replies, interest acquisition and
rejection, capacity-based dropping, proactive topic selection, and the HTTP/static-page boundary.

## Existing Telegram implementation

The 2025 bot remains under `src/`:

- `src/app.py` — LLM call, response splitting, randomized delays;
- `src/router.py` — Telegram commands and chat handler;
- `src/bot.py` — aiogram/Botspot polling process;
- `dev/chat_coordinator*` — earlier event-queue prototypes that were never wired into the bot.

That path still needs Telegram and LLM credentials plus the floating Botspot/Calmlib dependencies.
The local demo is intentionally a safe way to judge the product idea before reviving deployment.
