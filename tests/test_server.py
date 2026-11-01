import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from confab_ledger import Ledger
from confab_ledger.demo import seed_demo
from confab_ledger.server import handler_factory


class LocalHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        db = Path(cls.tempdir.name) / "api.sqlite3"
        with Ledger(db) as ledger:
            seed_demo(ledger)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(db))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.tempdir.cleanup()

    def get(self, route):
        with urlopen(self.base + route) as resp:
            return resp.status, json.load(resp)

    def test_state_contains_canon_and_provenance(self):
        status, state = self.get("/api/state?at=1875-04-20")
        self.assertEqual(status, 200)
        self.assertEqual(state["canon"][0]["value"], "yellow")
        self.assertTrue(any(ev["event_type"] == "CLAIM_DECIDED"
                            for ev in state["events"]))

    def test_character_query_keeps_hearsay_attributed(self):
        status, view = self.get("/api/character?id=ada&at=1875-04-20")
        self.assertEqual(status, 200)
        self.assertTrue(view["attributed_claims"][0]["heard"])
        self.assertEqual(view["known_canon"][0]["value"], "yellow")

    def test_structured_post_is_adjudicated(self):
        payload = dict(speaker="bill", subject="bill", predicate="favorite_food",
                       value="porridge", text="I enjoy porridge.",
                       effective_date="1875-04-20")
        req = Request(self.base + "/api/claims", data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req) as resp:
            body = json.load(resp)
            self.assertEqual(resp.status, 201)
        self.assertEqual(body["decision"]["status"], "CANON")

    def test_cross_site_origin_is_rejected(self):
        req = Request(self.base + "/api/claims", data=b"{}",
                      headers={"Origin": "https://untrusted.example"}, method="POST")
        with self.assertRaises(HTTPError) as err:
            urlopen(req)
        self.assertEqual(err.exception.code, 403)

    def test_dashboard_serves_html(self):
        with urlopen(self.base + "/") as resp:
            html = resp.read().decode()
        self.assertIn("Confabulation Ledger", html)
        self.assertIn("Adjudicate and append", html)


if __name__ == "__main__":
    unittest.main()
