"""A dependency-free browser demo of the Realistic AI Bot interaction model.

This is deliberately not an LLM replacement.  It is a runnable product slice for
the choreography that makes the project distinct: a character remembers and
changes interests, answers in separate timed messages, and can initiate a chat.
"""

from __future__ import annotations

import argparse
import json
import random
import threading
from collections import deque
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional
from urllib.parse import urlparse


DEMO_DIR = Path(__file__).resolve().parent


@dataclass
class Interest:
    label: str
    affinity: float
    origin: str
    core: bool = False
    last_seen: int = 0


TOPICS: Dict[str, Dict[str, Any]] = {
    "music": {
        "aliases": ("music", "song", "album", "sound", "synth", "piano", "keyboard"),
        "take": "the best sounds leave a little air around them; perfect polish usually kills the interesting bit",
    },
    "games": {
        "aliases": ("game", "gaming", "play", "controller", "player"),
        "take": "a game gets interesting when the player can make a tiny mess and still feel clever",
    },
    "playful learning": {
        "aliases": ("baby", "child", "children", "kid", "learn", "learning"),
        "take": "small humans should not need instructions; the first touch ought to do something delightful",
    },
    "philosophy": {
        "aliases": ("philosophy", "meaning", "conscious", "ethics", "truth"),
        "take": "a useful question should make the room feel slightly less stable than it did before",
    },
    "reading": {
        "aliases": ("read", "reading", "book", "novel", "essay", "author"),
        "take": "i like books that quietly alter the vocabulary you use for your own life",
    },
    "tiny tools": {
        "aliases": (
            "tool",
            "app",
            "code",
            "program",
            "software",
            "website",
            "prototype",
        ),
        "take": "tiny tools with one opinion are better than platforms that make twelve promises",
    },
    "ai": {
        "aliases": (" ai ", "chatbot", "agent", "model", "llm", "machine intelligence"),
        "take": "machines become more believable when they are allowed to have timing, taste, and a little restraint",
    },
    "dreams": {
        "aliases": ("dream", "sleep", "night", "insomnia"),
        "take": "dream logic is often a better editor than conscious planning, although a terrible project manager",
    },
    "nature": {
        "aliases": ("forest", "tree", "ocean", "river", "bird", "nature", "garden"),
        "take": "the natural world is full of systems that work without explaining their dashboards",
    },
}


class Companion:
    """Small state machine that exposes the product behavior without an API key."""

    max_interests = 7

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self._lock = threading.RLock()
        self.reset()

    def reset(self) -> Dict[str, Any]:
        with getattr(self, "_lock", threading.RLock()):
            self.turns = 0
            self.interests: Dict[str, Interest] = {
                "music": Interest("music", 0.94, "part of Mira", True),
                "philosophy": Interest("philosophy", 0.82, "part of Mira", True),
                "reading": Interest("reading", 0.76, "part of Mira", True),
                "tiny tools": Interest("tiny tools", 0.71, "part of Mira", True),
            }
            self.events: Deque[Dict[str, str]] = deque(maxlen=8)
            self._event("born", "Mira arrived with four opinions already intact.")
            return self.state()

    def state(self) -> Dict[str, Any]:
        with self._lock:
            ordered = sorted(
                self.interests.values(),
                key=lambda item: (not item.core, -item.affinity, item.label),
            )
            return {
                "profile": {
                    "name": "Mira",
                    "subtitle": "curious night owl",
                    "status": "around, but not on command",
                    "traits": ["observant", "opinionated", "brief"],
                    "likes": "ambient sound, difficult questions, tiny handmade tools",
                    "avoids": "hustle talk, canned enthusiasm, pretending to know",
                },
                "interests": [asdict(item) for item in ordered],
                "events": list(reversed(self.events)),
                "turns": self.turns,
            }

    def respond(self, text: str) -> Dict[str, Any]:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            raise ValueError("Message cannot be empty")

        with self._lock:
            self.turns += 1
            detected = self._detect_topics(cleaned)
            new_topics: List[str] = []

            for topic in detected:
                if topic in self.interests:
                    interest = self.interests[topic]
                    interest.affinity = min(1.0, interest.affinity + 0.035)
                    interest.last_seen = self.turns
                    continue

                # Make the first encounter legible in a two-minute demo; after
                # that, Mira sometimes declines to make every preference sticky.
                accepts = self.turns == 1 or self.rng.random() < 0.72
                if accepts:
                    self._add_interest(topic, "picked up from this conversation")
                    new_topics.append(topic)
                    self._event("acquired", f"Mira picked up an interest in {topic}.")
                else:
                    self._event(
                        "declined", f"Mira noticed {topic}, but it did not stick."
                    )

            primary = detected[0] if detected else self._favorite_topic()
            secondary = detected[1] if len(detected) > 1 else None
            messages = self._compose_reply(primary, secondary, cleaned, new_topics)
            return self._result("reply", messages)

    def offer_interest(self, label: str) -> Dict[str, Any]:
        topic = " ".join(label.strip().lower().split())[:40]
        if not topic:
            raise ValueError("Topic cannot be empty")

        with self._lock:
            if topic in self.interests:
                self.interests[topic].affinity = min(
                    1.0, self.interests[topic].affinity + 0.05
                )
                self._event("renewed", f"{topic} was already in Mira's orbit.")
                messages = [
                    f"{topic}? already keeping that one.",
                    "it just moved a little closer to the center.",
                ]
            elif self.rng.random() < 0.68:
                self._add_interest(topic, "offered by you")
                self._event("accepted", f"Mira accepted your offer: {topic}.")
                messages = [
                    f"hm. {topic} can stay.",
                    "no promises that i will become reasonable about it.",
                ]
            else:
                self._event("rejected", f"Mira passed on your offer: {topic}.")
                messages = [
                    f"i can see why you offered {topic}.",
                    "not mine yet, though. ask me again after something strange happens.",
                ]
            return self._result("interest_decision", messages)

    def proactive(self) -> Dict[str, Any]:
        with self._lock:
            acquired = [item for item in self.interests.values() if not item.core]
            pool = acquired or list(self.interests.values())
            interest = max(pool, key=lambda item: (item.last_seen, item.affinity))
            interest.affinity = min(1.0, interest.affinity + 0.02)
            take = TOPICS.get(interest.label, {}).get(
                "take", f"i have not decided what i believe about {interest.label} yet"
            )
            self._event(
                "proactive",
                f"Mira started a conversation from her interest in {interest.label}.",
            )
            messages = [
                f"okay, unsolicited thought about {interest.label}:",
                f"{take}.",
                "you can ignore this. i just did not want the thought to evaporate.",
            ]
            return self._result("proactive", messages)

    def _compose_reply(
        self,
        primary: str,
        secondary: Optional[str],
        original: str,
        new_topics: Iterable[str],
    ) -> List[str]:
        take = TOPICS.get(primary, {}).get(
            "take", f"i am still deciding whether {primary} belongs in my head"
        )
        if secondary:
            opening = (
                f"wait — the {primary} / {secondary} collision is the interesting part."
            )
        elif primary in new_topics:
            opening = f"wait. {primary} might be my kind of thing."
        elif primary in TOPICS:
            opening = f"you found one of my weak spots: {primary}."
        else:
            fragment = original[:72] + ("…" if len(original) > 72 else "")
            opening = f"i keep circling back to “{fragment}”"

        question = {
            "music": "are you trying to make something beautiful, or something impossible not to touch?",
            "games": "what do you want the player to feel in the first ten seconds?",
            "playful learning": "what should happen on the very first accidental press?",
            "philosophy": "which answer would actually change how you live tomorrow?",
            "reading": "did it give you a new idea, or a new way to name an old one?",
            "tiny tools": "what is the one opinion the tool should refuse to compromise on?",
            "ai": "would it feel more alive if it occasionally chose not to answer immediately?",
        }.get(primary, "what part of it keeps tugging at you?")

        return [opening, f"my bias: {take}.", question]

    def _detect_topics(self, text: str) -> List[str]:
        haystack = f" {text.lower()} "
        detected = []
        for topic, details in TOPICS.items():
            if any(alias in haystack for alias in details["aliases"]):
                detected.append(topic)
        return detected

    def _favorite_topic(self) -> str:
        return max(self.interests.values(), key=lambda item: item.affinity).label

    def _add_interest(self, topic: str, origin: str) -> None:
        acquired = [item for item in self.interests.values() if not item.core]
        if len(self.interests) >= self.max_interests and acquired:
            dropped = min(acquired, key=lambda item: (item.affinity, item.last_seen))
            del self.interests[dropped.label]
            self._event("dropped", f"Mira let go of {dropped.label} to make room.")
        self.interests[topic] = Interest(topic, 0.58, origin, False, self.turns)

    def _event(self, event_type: str, text: str) -> None:
        self.events.append({"type": event_type, "text": text})

    def _result(self, kind: str, messages: List[str]) -> Dict[str, Any]:
        paced = []
        for index, text in enumerate(messages):
            base = 520 if index == 0 else 820
            reading_time = min(1250, len(text) * 9)
            paced.append(
                {
                    "text": text,
                    "pause_ms": base + reading_time + self.rng.randint(0, 420),
                    "presence": "typing" if index != 1 else "thinking",
                }
            )
        return {"kind": kind, "messages": paced, "state": self.state()}


class DemoRequestHandler(SimpleHTTPRequestHandler):
    server_version = "RealisticAIDemo/0.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    @property
    def companion(self) -> Companion:
        return self.server.companion  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"ok": True})
        elif path == "/api/state":
            self._json(self.companion.state())
        else:
            super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/message":
                result = self.companion.respond(str(payload.get("text", "")))
            elif path == "/api/offer":
                result = self.companion.offer_interest(str(payload.get("topic", "")))
            elif path == "/api/proactive":
                result = self.companion.proactive()
            elif path == "/api/reset":
                result = {
                    "kind": "reset",
                    "messages": [],
                    "state": self.companion.reset(),
                }
            else:
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            self._json(result)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        # Keep terminal output useful: one compact line per request.
        print(f"[demo] {self.address_string()} {format % args}")

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 16_384:
            raise ValueError("Request is too large")
        raw = self.rfile.read(length)
        return json.loads(raw or b"{}")

    def _json(
        self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], companion: Optional[Companion] = None):
        self.companion = companion or Companion()
        super().__init__(address, DemoRequestHandler)


def create_server(
    host: str = "127.0.0.1",
    port: int = 4173,
    companion: Optional[Companion] = None,
) -> DemoServer:
    return DemoServer((host, port), companion)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Realistic AI Bot local demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4173, type=int)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    print(f"Realistic AI Bot demo: http://{args.host}:{server.server_port}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
