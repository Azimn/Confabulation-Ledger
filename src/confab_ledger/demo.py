"""Seed a tiny fictional world with documented, reviewable evidence."""

from datetime import date

from .ledger import Ledger


def seed_demo(ledger: Ledger) -> dict:
    if ledger.events():
        return {"seeded": False, "reason": "ledger already contains events"}
    ledger.register_entity("bill", "Bill", "bill")
    ledger.register_entity("mara", "Mara, Bill's wife", "mara",
                           delegations={"bill": ["hair_color"]},
                           protected=["marital_status"])
    ledger.register_entity("ada", "Ada, a neighbor", "ada")
    first = ledger.propose(
        speaker="bill", subject="mara", predicate="hair_color", value="yellow",
        text="My wife has yellow hair.", effective_date="1875-04-01",
        source_key="demo:conversation-1:turn-1")
    second = ledger.propose(
        speaker="bill", subject="mara", predicate="hair_color", value="black",
        text="My wife always had black hair.", effective_date="1875-04-15",
        speech_act="recollection", source_key="demo:conversation-2:turn-1")
    ledger.hear(claim_id=second["claim"]["claim_id"], listener="ada",
                context="Bill told Ada in the marketplace")
    ledger.propose(speaker="ada", subject="mara", predicate="keepsake",
                   value="silver locket", text="I suppose Mara owns a silver locket.",
                   effective_date="1875-04-20", speech_act="uncertain")
    return {"seeded": True, "yellow_claim": first["claim"]["claim_id"],
            "disputed_claim": second["claim"]["claim_id"]}
