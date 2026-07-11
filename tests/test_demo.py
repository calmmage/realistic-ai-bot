import json
import random
import threading
import unittest
from urllib.request import Request, urlopen

from demo.server import Companion, create_server


class CompanionTests(unittest.TestCase):
    def test_starts_with_a_specific_character_and_core_interests(self):
        state = Companion(random.Random(1)).state()

        self.assertEqual(state["profile"]["name"], "Mira")
        self.assertIn("opinionated", state["profile"]["traits"])
        self.assertEqual(
            [item["label"] for item in state["interests"] if item["core"]],
            ["music", "philosophy", "reading", "tiny tools"],
        )

    def test_reply_is_multiple_paced_messages_and_acquires_topics(self):
        companion = Companion(random.Random(1))

        result = companion.respond(
            "I am merging a baby keyboard with a strange game and music generator."
        )

        self.assertEqual(result["kind"], "reply")
        self.assertGreaterEqual(len(result["messages"]), 2)
        self.assertTrue(all(part["pause_ms"] > 0 for part in result["messages"]))
        self.assertEqual(
            {part["presence"] for part in result["messages"]}, {"typing", "thinking"}
        )
        interest_names = {item["label"] for item in result["state"]["interests"]}
        self.assertIn("games", interest_names)
        self.assertIn("playful learning", interest_names)

    def test_interest_offer_can_be_accepted_or_rejected(self):
        accepted = Companion(random.Random(1)).offer_interest("brutalism")
        rejected = Companion(random.Random(2)).offer_interest("brutalism")

        self.assertIn(
            "brutalism", {item["label"] for item in accepted["state"]["interests"]}
        )
        self.assertNotIn(
            "brutalism", {item["label"] for item in rejected["state"]["interests"]}
        )
        self.assertEqual(accepted["state"]["events"][0]["type"], "accepted")
        self.assertEqual(rejected["state"]["events"][0]["type"], "rejected")

    def test_proactive_message_uses_a_recently_acquired_interest(self):
        companion = Companion(random.Random(1))
        companion.respond("I am making a game for a baby.")

        result = companion.proactive()

        self.assertEqual(result["kind"], "proactive")
        combined = " ".join(part["text"] for part in result["messages"])
        self.assertTrue("games" in combined or "playful learning" in combined)
        self.assertEqual(result["state"]["events"][0]["type"], "proactive")

    def test_acquired_interest_capacity_drops_oldest_non_core_topic(self):
        companion = Companion(random.Random(1))
        companion._add_interest("one", "test")
        companion._add_interest("two", "test")
        companion._add_interest("three", "test")
        companion._add_interest("four", "test")

        names = set(companion.interests)
        self.assertEqual(len(names), companion.max_interests)
        self.assertNotIn("one", names)
        self.assertIn("four", names)


class DemoHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0, companion=Companion(random.Random(1)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_and_static_page(self):
        with urlopen(f"{self.base_url}/api/health") as response:
            self.assertEqual(json.load(response), {"ok": True})

        with urlopen(f"{self.base_url}/") as response:
            page = response.read().decode("utf-8")
        self.assertIn("skip ahead until she texts", page)
        self.assertIn("live inner state", page)

    def test_message_endpoint_returns_choreography_and_state(self):
        request = Request(
            f"{self.base_url}/api/message",
            data=json.dumps({"text": "A game about dreams"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.load(response)

        self.assertEqual(payload["kind"], "reply")
        self.assertEqual(len(payload["messages"]), 3)
        self.assertGreaterEqual(payload["state"]["turns"], 1)


if __name__ == "__main__":
    unittest.main()
