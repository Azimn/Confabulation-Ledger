"""Re-run the labeled micro-world decision corpus with no LLM calls."""

import json
from pathlib import Path
from confab_ledger import Ledger

BENCHMARK = Path(__file__).resolve().parent.parent / "benchmarks" / "micro_world_v0.json"


def replay(path=BENCHMARK):
    suite = json.loads(Path(path).read_text())
    passed = []
    for case in suite["cases"]:
        with Ledger() as ledger:
            ledger.register_entity("bill", "Bill", "bill")
            ledger.register_entity("mara", "Mara", "mara", delegations={"bill": ["hair_color"]},
                                   protected=["marital_status"])
            ledger.register_entity("ada", "Ada", "ada")
            for i, setup in enumerate(case.get("setup", [])):
                if setup["type"] == "claim":
                    ledger.propose(speaker="bill", subject=setup["subject"],
                                   predicate=setup["predicate"], value=setup["value"],
                                   text="Preexisting fact", effective_date="1875-03-01")
                elif setup["type"] == "world_event":
                    ledger.record_world_event(receipt_id=f"setup-{i}",
                        subject=setup["subject"], predicate=setup["predicate"],
                        value=setup["value"], effective_date=setup["effective_date"],
                        evidence="trusted benchmark world event")
                else:
                    raise ValueError("unknown setup type")
            result = ledger.propose(**case["candidate"])
            found = result["decision"]["status"]
            assert found == case["expected_status"], (
                f"{case['id']}: expected {case['expected_status']}, got {found}")
            if "viewer" in case:
                facts = ledger.canon_at(case["candidate"]["effective_date"],
                                        viewer=case["viewer"])
                assert len(facts) == case["expected_viewer_fact_count"], case["id"]
            passed.append(case["id"])
    return passed


if __name__ == "__main__":
    cases = replay()
    print(f"PASS {len(cases)}/{len(cases)} deterministic policy cases")
