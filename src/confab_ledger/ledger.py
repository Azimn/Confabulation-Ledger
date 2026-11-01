"""Append-only narrative history and a conservative, replayable canon policy.

An utterance is proof of an utterance, never proof of the utterance's truth.
World observations can only be appended by a trusted local simulation caller.
This module makes no model calls and does not parse free text.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


class LedgerError(ValueError):
    """Invalid or unauthorized ledger operation."""


LOW_IMPACT = frozenset({
    "hair_color", "eye_color", "favorite_food", "favorite_book", "hobby",
    "preferred_name", "favorite_color", "keepsake", "usual_drink",
    "favorite_song", "favorite_flower", "favorite_season",
})
SPEECH_ACTS = frozenset({
    "assertion", "recollection", "hearsay", "wish", "dream", "hypothetical",
    "joke", "lie", "question", "uncertain",
})
DISPOSITIONS = frozenset({"CANON", "BELIEF_ONLY", "PENDING", "REJECTED"})
SOURCE_TYPES = frozenset({"dialogue", "dream", "diary", "book", "hearsay", "narration", "observation"})


def _date(value: str) -> str:
    if not isinstance(value, str):
        raise LedgerError("effective_date must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise LedgerError("effective_date must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise LedgerError("effective_date must be YYYY-MM-DD")
    return value


def _required(value: Any, field: str, limit: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise LedgerError(f"{field} must be a nonempty string (max {limit} characters)")
    return value


def _beat(timestamp: datetime) -> str:
    """Swatch Internet Time, UTC+1: @000 through @999."""
    seconds = (timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second
               + timestamp.microsecond / 1_000_000 + 3600) % 86400
    return f"@{int(seconds / 86.4):03d}"


class Ledger:
    """Small single-world event store; new connections can read the same SQLite file."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(path), isolation_level=None, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                recorded_at_utc TEXT NOT NULL,
                swatch_beat TEXT NOT NULL
            )
        """)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Ledger:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _append(self, kind: str, payload: dict[str, Any]) -> int:
        now = datetime.now(timezone.utc)
        cursor = self.conn.execute(
            "INSERT INTO events(event_type,payload,recorded_at_utc,swatch_beat) "
            "VALUES(?,?,?,?)",
            (kind, json.dumps(payload, sort_keys=True, ensure_ascii=False),
             now.isoformat(timespec="microseconds"), _beat(now)),
        )
        return int(cursor.lastrowid)

    def events(self) -> list[dict[str, Any]]:
        return [{"seq": r["seq"], "event_type": r["event_type"],
                 "payload": json.loads(r["payload"]),
                 "recorded_at_utc": r["recorded_at_utc"],
                 "swatch_beat": r["swatch_beat"]}
                for r in self.conn.execute("SELECT * FROM events ORDER BY seq")]

    def entities(self) -> dict[str, dict[str, Any]]:
        return {ev["payload"]["id"]: ev["payload"]
                for ev in self.events() if ev["event_type"] == "ENTITY_REGISTERED"}

    def register_entity(self, entity_id: str, name: str, owner: str,
                        *, protected: list[str] | None = None,
                        delegations: dict[str, list[str]] | None = None) -> None:
        """Declare a fictional entity and explicit delegated predicate authorities.

        owner is a character ID or 'author'; this is setup-time trusted configuration.
        """
        entity_id = _required(entity_id, "entity_id")
        name = _required(name, "name")
        owner = _required(owner, "owner")
        delegations = delegations or {}
        protected = protected or []
        if (not isinstance(protected, list) or not all(isinstance(x, str) for x in protected)
                or not isinstance(delegations, dict)
                or not all(isinstance(k, str) and isinstance(v, list)
                           and all(isinstance(x, str) for x in v)
                           for k, v in delegations.items())):
            raise LedgerError("invalid protected predicates or delegations")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            if entity_id in self.entities():
                raise LedgerError("entity ID already registered")
            self._append("ENTITY_REGISTERED", {"id": entity_id, "name": name,
                "owner": owner, "protected": protected, "delegations": delegations})
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def _claims_and_decisions(self) -> tuple[dict[str, dict], dict[str, dict]]:
        claims: dict[str, dict] = {}
        decisions: dict[str, dict] = {}
        for ev in self.events():
            p = ev["payload"]
            if ev["event_type"] == "CLAIM_SUBMITTED":
                claims[p["claim_id"]] = p
            elif ev["event_type"] in ("CLAIM_DECIDED", "CLAIM_REVIEWED"):
                decisions[p["claim_id"]] = {**p, "decision_seq": ev["seq"]}
        return claims, decisions

    def canon_at(self, at: str, viewer: str | None = None) -> list[dict[str, Any]]:
        """Derive time-qualified world state; filter inaccessible private facts.

        None viewer means an omniscient, trusted research/operator view.
        """
        _date(at)
        claims, decisions = self._claims_and_decisions()
        entities = self.entities()
        candidates: list[dict[str, Any]] = []
        for claim_id, decision in decisions.items():
            if decision["status"] == "CANON":
                c = claims[claim_id]
                candidates.append({"subject": c["subject"], "predicate": c["predicate"],
                    "value": c["value"], "effective_date": c["effective_date"],
                    "visibility": c["visibility"], "source_type": "claim",
                    "source_id": claim_id, "speaker": c["speaker"],
                    "order": decision["decision_seq"]})
        for ev in self.events():
            p = ev["payload"]
            if ev["event_type"] in ("WORLD_EVENT", "EDITOR_OVERRIDE"):
                candidates.append({"subject": p["subject"], "predicate": p["predicate"],
                    "value": p["value"], "effective_date": p["effective_date"],
                    "visibility": p["visibility"], "source_type": ev["event_type"].lower(),
                    "source_id": p["receipt_id"], "speaker": p["actor"],
                    "order": ev["seq"]})
        candidates.sort(key=lambda c: (c["effective_date"], c["order"]))
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for item in candidates:
            if item["effective_date"] <= at:
                latest[(item["subject"], item["predicate"])] = item
        output = []
        for fact in latest.values():
            subject = entities.get(fact["subject"], {})
            if viewer is not None and fact["visibility"] == "private":
                if viewer not in {subject.get("owner"), fact["speaker"]}:
                    continue
            output.append(fact)
        return sorted(output, key=lambda f: (f["subject"], f["predicate"]))

    def claim_status(self, claim_id: str) -> dict[str, Any] | None:
        _, decisions = self._claims_and_decisions()
        return decisions.get(claim_id)

    def propose(self, *, speaker: str, subject: str, predicate: str,
                value: str, text: str, effective_date: str,
                speech_act: str = "assertion", visibility: str = "public",
                reference_status: str = "resolved", context: str = "",
                source_type: str = "dialogue", source_key: str = "") -> dict[str, Any]:
        """Add an utterance, then adjudicate it under the current deterministic policy.

        Parameters are structured extraction output, NOT verified claims.
        """
        fields = {k: _required(v, k, 2000 if k in ("text", "context") else 200)
                  for k, v in {"speaker": speaker, "subject": subject,
                    "predicate": predicate, "value": value, "text": text,
                    "source_type": source_type}.items()}
        if context and (not isinstance(context, str) or len(context) > 2000):
            raise LedgerError("context must be a string (max 2000 characters)")
        if source_key and (not isinstance(source_key, str) or len(source_key) > 200):
            raise LedgerError("source_key must be a short string")
        if speech_act not in SPEECH_ACTS:
            raise LedgerError("unknown speech_act")
        if source_type not in SOURCE_TYPES:
            raise LedgerError("unknown source_type")
        if visibility not in ("public", "private"):
            raise LedgerError("visibility must be public or private")
        if reference_status not in ("resolved", "ambiguous"):
            raise LedgerError("reference_status must be resolved or ambiguous")
        _date(effective_date)
        claim = {**fields, "claim_id": str(uuid.uuid4()), "effective_date": effective_date,
                 "speech_act": speech_act, "visibility": visibility,
                 "reference_status": reference_status, "context": context,
                 "source_key": source_key}
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            entities = self.entities()
            existing = next((f for f in self.canon_at(effective_date)
                             if f["subject"] == subject and f["predicate"] == predicate), None)
            if speaker not in entities or subject not in entities:
                status, reason = "PENDING", "unknown fictional speaker or subject"
            elif reference_status == "ambiguous":
                status, reason = "PENDING", "entity reference unresolved"
            elif source_type != "dialogue":
                status, reason = "BELIEF_ONLY", f"{source_type} source is not direct dialogue evidence"
            elif speech_act not in ("assertion", "recollection"):
                status, reason = "BELIEF_ONLY", f"speech act {speech_act} is not world evidence"
            elif predicate in entities[subject]["protected"]:
                status, reason = "PENDING", "creator-protected predicate"
            elif predicate not in LOW_IMPACT:
                status, reason = "PENDING", "not on the low-impact auto-promotion allowlist"
            elif not (speaker == entities[subject]["owner"]
                      or predicate in entities[subject]["delegations"].get(speaker, [])):
                status, reason = "PENDING", "speaker lacks authority over subject/predicate"
            elif existing is not None and existing["value"] != value:
                status, reason = "BELIEF_ONLY", "contradicts the established world timeline"
            elif existing is not None:
                status, reason = "BELIEF_ONLY", "consistent restatement; no new world fact"
            else:
                # Conservative temporal rule: an unreceipted claim must not rewrite
                # earlier or later observed state, even if the assertion is backdated.
                known = [f for ev in self.events() for f in [ev] if
                         ev["event_type"] in ("WORLD_EVENT", "EDITOR_OVERRIDE")
                         and ev["payload"]["subject"] == subject
                         and ev["payload"]["predicate"] == predicate]
                accepted, decisions = self._claims_and_decisions()
                known.extend({"payload": accepted[cid]} for cid, d in decisions.items()
                             if d["status"] == "CANON"
                             and accepted[cid]["subject"] == subject
                             and accepted[cid]["predicate"] == predicate)
                if known:
                    status, reason = "PENDING", "historical/future state exists; requires review"
                else:
                    status, reason = "CANON", "open low-impact fact within delegated authority"
            self._append("CLAIM_SUBMITTED", claim)
            decision = {"claim_id": claim["claim_id"], "status": status,
                        "reason": reason, "policy": "deterministic-v0.1",
                        "reviewer": "policy-engine"}
            self._append("CLAIM_DECIDED", decision)
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        return {"claim": claim, "decision": decision}

    def review(self, claim_id: str, status: str, *, rationale: str,
               reviewer: str = "author") -> dict[str, Any]:
        """Human redecision; original utterance and earlier decisions remain immutable."""
        if reviewer != "author":
            raise LedgerError("only the author can manually review")
        if status not in DISPOSITIONS:
            raise LedgerError("invalid disposition")
        _required(rationale, "rationale", 2000)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            claims, _ = self._claims_and_decisions()
            if claim_id not in claims:
                raise LedgerError("unknown claim ID")
            decision = {"claim_id": claim_id, "status": status,
                        "reason": rationale, "policy": "human-review",
                        "reviewer": reviewer}
            self._append("CLAIM_REVIEWED", decision)
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        return decision

    def record_world_event(self, *, receipt_id: str, subject: str,
                           predicate: str, value: str, effective_date: str,
                           evidence: str, visibility: str = "public",
                           actor: str = "simulation") -> None:
        """Trusted host integration only. Never expose this method to an LLM API.

        A receipt is a host-attested causal event, not a claim's narrative text.
        """
        if actor != "simulation":
            raise LedgerError("world events require the trusted simulation actor")
        payload = {k: _required(v, k, 2000 if k == "evidence" else 200)
                   for k, v in {"receipt_id": receipt_id, "subject": subject,
                       "predicate": predicate, "value": value, "evidence": evidence,
                       "actor": actor}.items()}
        payload["effective_date"] = _date(effective_date)
        if visibility not in ("public", "private"):
            raise LedgerError("invalid visibility")
        payload["visibility"] = visibility
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            if subject not in self.entities():
                raise LedgerError("unknown entity")
            if any(ev["payload"].get("receipt_id") == receipt_id
                   for ev in self.events()):
                raise LedgerError("duplicate receipt ID")
            self._append("WORLD_EVENT", payload)
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def override(self, *, receipt_id: str, subject: str, predicate: str,
                 value: str, effective_date: str, rationale: str,
                 visibility: str = "public", actor: str = "author") -> None:
        if actor != "author":
            raise LedgerError("only the author can override canon")
        _required(rationale, "rationale", 2000)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            if subject not in self.entities():
                raise LedgerError("unknown entity")
            if any(e["payload"].get("receipt_id") == receipt_id for e in self.events()):
                raise LedgerError("duplicate receipt ID")
            for k, v in {"receipt_id": receipt_id, "predicate": predicate, "value": value}.items():
                _required(v, k)
            _date(effective_date)
            if visibility not in ("public", "private"):
                raise LedgerError("invalid visibility")
            self._append("EDITOR_OVERRIDE", {"receipt_id": receipt_id,
                "subject": subject, "predicate": predicate, "value": value,
                "effective_date": effective_date, "rationale": rationale,
                "visibility": visibility, "actor": actor})
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def hear(self, *, claim_id: str, listener: str, context: str = "") -> None:
        """Record transmission of a claim, without promoting its truth."""
        _required(context or "encounter", "context", 2000)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            claims, _ = self._claims_and_decisions()
            if claim_id not in claims or listener not in self.entities():
                raise LedgerError("unknown claim or listener")
            self._append("CLAIM_HEARD", {"claim_id": claim_id,
                "listener": listener, "context": context})
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def character_view(self, character_id: str, at: str) -> dict[str, Any]:
        if character_id not in self.entities():
            raise LedgerError("unknown character")
        claims, decisions = self._claims_and_decisions()
        heard = {e["payload"]["claim_id"] for e in self.events()
                 if e["event_type"] == "CLAIM_HEARD"
                 and e["payload"]["listener"] == character_id}
        attributed = []
        for cid, c in claims.items():
            if c["effective_date"] > _date(at):
                continue
            if c["speaker"] == character_id or cid in heard:
                attributed.append({"claim_id": cid, "text": c["text"],
                    "speaker": c["speaker"], "subject": c["subject"],
                    "predicate": c["predicate"], "value": c["value"],
                    "speech_act": c["speech_act"], "status": decisions[cid]["status"],
                    "heard": cid in heard and c["speaker"] != character_id})
        return {"character": character_id,
                "known_canon": self.canon_at(at, viewer=character_id),
                "attributed_claims": attributed}

    def snapshot(self, at: str) -> dict[str, Any]:
        claims, decisions = self._claims_and_decisions()
        return {"as_of": _date(at), "entities": list(self.entities().values()),
                "canon": self.canon_at(at),
                "claims": [{**c, "decision": decisions[cid]} for cid, c in claims.items()],
                "events": self.events()}
