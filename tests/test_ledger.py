import tempfile
import unittest
from pathlib import Path

from confab_ledger import Ledger, LedgerError
from confab_ledger.demo import seed_demo


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.ledger = Ledger(self.path)
        self.ledger.register_entity("bill", "Bill", "bill")
        self.ledger.register_entity("mara", "Mara", "mara",
            delegations={"bill": ["hair_color"]}, protected=["marital_status"])
        self.ledger.register_entity("ada", "Ada", "ada")

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def claim(self, **kw):
        args = dict(speaker="bill", subject="mara", predicate="hair_color",
                    value="yellow", text="My wife has yellow hair.",
                    effective_date="1875-04-01")
        args.update(kw)
        return self.ledger.propose(**args)

    def test_open_delegated_detail_becomes_canon(self):
        r = self.claim()
        self.assertEqual(r["decision"]["status"], "CANON")
        self.assertEqual(self.ledger.canon_at("1875-04-02")[0]["value"], "yellow")

    def test_claim_and_decision_are_separate_append_only_events(self):
        self.claim()
        events = self.ledger.events()
        self.assertEqual([e["event_type"] for e in events[-2:]],
                         ["CLAIM_SUBMITTED", "CLAIM_DECIDED"])
        self.assertEqual(events[-2]["payload"]["text"], "My wife has yellow hair.")
        self.assertRegex(events[-1]["swatch_beat"], r"^@\d{3}$")

    def test_conflict_retains_bills_recollection_but_not_world_state(self):
        self.claim()
        r = self.claim(value="black", text="My wife always had black hair.",
                       speech_act="recollection", effective_date="1875-04-15")
        self.assertEqual(r["decision"]["status"], "BELIEF_ONLY")
        self.assertEqual(self.ledger.canon_at("1875-04-20")[0]["value"], "yellow")
        view = self.ledger.character_view("bill", "1875-04-20")
        self.assertEqual(len(view["attributed_claims"]), 2)
        self.assertEqual(view["attributed_claims"][1]["value"], "black")

    def test_temporal_change_requires_receipt(self):
        self.claim()
        self.assertEqual(self.claim(value="black", effective_date="1875-06-01")
                         ["decision"]["status"], "BELIEF_ONLY")
        self.ledger.record_world_event(receipt_id="dye-1", subject="mara",
            predicate="hair_color", value="black", effective_date="1875-05-01",
            evidence="trusted simulation hair-dyeing event")
        self.assertEqual(self.ledger.canon_at("1875-04-30")[0]["value"], "yellow")
        self.assertEqual(self.ledger.canon_at("1875-05-01")[0]["value"], "black")

    def test_dream_not_canon(self):
        self.assertEqual(self.claim(speech_act="dream")["decision"]["status"],
                         "BELIEF_ONLY")
        self.assertEqual(self.ledger.canon_at("1875-04-02"), [])

    def test_dream_source_cannot_pose_as_plain_assertion(self):
        self.assertEqual(self.claim(source_type="dream", speech_act="assertion")
                         ["decision"]["status"], "BELIEF_ONLY")

    def test_hearsay_not_canon(self):
        self.assertEqual(self.claim(speech_act="hearsay")["decision"]["status"],
                         "BELIEF_ONLY")
        self.assertEqual(self.ledger.canon_at("1875-04-02"), [])

    def test_lies_wishes_jokes_hypotheticals_not_canon(self):
        for act in ("lie", "wish", "joke", "hypothetical", "question", "uncertain"):
            with self.subTest(act=act):
                self.assertEqual(self.claim(speech_act=act)["decision"]["status"],
                                 "BELIEF_ONLY")
        self.assertEqual(self.ledger.canon_at("1875-04-20"), [])

    def test_unauthorized_cross_character_history_is_pending(self):
        self.assertEqual(self.claim(speaker="ada")["decision"]["status"], "PENDING")

    def test_creator_protection_takes_precedence(self):
        r = self.claim(subject="mara", predicate="marital_status", value="widowed")
        self.assertEqual(r["decision"]["status"], "PENDING")
        self.assertIn("protected", r["decision"]["reason"])

    def test_nontrivial_world_event_is_pending(self):
        self.assertEqual(self.claim(predicate="owns_castle", value="yes")
                         ["decision"]["status"], "PENDING")

    def test_ambiguous_entity_not_resolved_silently(self):
        self.assertEqual(self.claim(reference_status="ambiguous")
                         ["decision"]["status"], "PENDING")

    def test_unknown_entity_pending(self):
        self.assertEqual(self.claim(subject="unknown")["decision"]["status"], "PENDING")

    def test_consistent_restatement_is_not_new_factual_evidence(self):
        self.claim()
        r = self.claim(source_key="same-interview-second-mention")
        self.assertEqual(r["decision"]["status"], "BELIEF_ONLY")
        self.assertEqual(len(self.ledger.canon_at("1875-04-20")), 1)

    def test_private_fact_filtered_for_other_character(self):
        self.claim(visibility="private")
        self.assertEqual(self.ledger.canon_at("1875-04-02", viewer="ada"), [])
        self.assertEqual(len(self.ledger.canon_at("1875-04-02", viewer="bill")), 1)
        self.assertEqual(len(self.ledger.canon_at("1875-04-02", viewer="mara")), 1)

    def test_rollback_keeps_audit_and_restores_view(self):
        r = self.claim()
        first = len(self.ledger.events())
        self.ledger.review(r["claim"]["claim_id"], "REJECTED", rationale="Erroneous extraction")
        self.assertEqual(self.ledger.canon_at("1875-04-20"), [])
        self.assertEqual(len(self.ledger.events()), first + 1)
        self.ledger.review(r["claim"]["claim_id"], "CANON", rationale="Manual verification")
        self.assertEqual(self.ledger.canon_at("1875-04-20")[0]["value"], "yellow")
        self.assertEqual(self.ledger.events()[-2]["event_type"], "CLAIM_REVIEWED")

    def test_only_author_can_review(self):
        r = self.claim()
        with self.assertRaises(LedgerError):
            self.ledger.review(r["claim"]["claim_id"], "REJECTED",
                               rationale="spoof", reviewer="bill")

    def test_restart_persists_every_record(self):
        self.claim()
        old_events = self.ledger.events()
        with Ledger(self.path) as reopened:
            self.assertEqual(old_events, reopened.events())
            self.assertEqual(reopened.canon_at("1875-04-20")[0]["value"], "yellow")

    def test_historical_backfill_cannot_sneak_past_future_fact(self):
        self.ledger.record_world_event(receipt_id="event-7", subject="mara",
            predicate="hair_color", value="black", effective_date="1875-05-01",
            evidence="observed change")
        result = self.claim(effective_date="1875-04-01")
        self.assertEqual(result["decision"]["status"], "PENDING")

    def test_override_is_a_separate_immutable_event(self):
        self.claim()
        self.ledger.override(receipt_id="edit-1", subject="mara", predicate="hair_color",
                             value="green", effective_date="1875-05-03", rationale="Author revision")
        self.assertEqual(self.ledger.canon_at("1875-04-20")[0]["value"], "yellow")
        self.assertEqual(self.ledger.canon_at("1875-05-03")[0]["value"], "green")
        self.assertEqual(self.ledger.events()[-1]["event_type"], "EDITOR_OVERRIDE")

    def test_hearing_disputed_claim_does_not_make_it_true(self):
        self.claim()
        rumor = self.claim(value="black", speech_act="hearsay")
        self.ledger.hear(claim_id=rumor["claim"]["claim_id"], listener="ada")
        view = self.ledger.character_view("ada", "1875-04-20")
        self.assertTrue(view["attributed_claims"][0]["heard"])
        self.assertEqual(view["known_canon"][0]["value"], "yellow")

    def test_no_duplicate_event_receipts(self):
        args = dict(receipt_id="evt1", subject="mara", predicate="hair_color",
                    value="black", effective_date="1875-05-01", evidence="observed")
        self.ledger.record_world_event(**args)
        with self.assertRaises(LedgerError):
            self.ledger.record_world_event(**args)

    def test_invalid_input_has_no_partial_submission(self):
        old = len(self.ledger.events())
        with self.assertRaises(LedgerError):
            self.claim(effective_date="yesterday")
        self.assertEqual(len(self.ledger.events()), old)

    def test_entity_cannot_be_duplicated(self):
        with self.assertRaises(LedgerError):
            self.ledger.register_entity("bill", "Not Bill", "bill")


class DemoTests(unittest.TestCase):
    def test_bills_story_is_replayable(self):
        with Ledger() as ledger:
            receipt = seed_demo(ledger)
            self.assertTrue(receipt["seeded"])
            self.assertFalse(seed_demo(ledger)["seeded"])
            self.assertEqual(ledger.canon_at("1875-04-20")[0]["value"], "yellow")
            self.assertEqual(ledger.character_view("ada", "1875-04-20")
                             ["attributed_claims"][0]["status"], "BELIEF_ONLY")


if __name__ == "__main__":
    unittest.main()
