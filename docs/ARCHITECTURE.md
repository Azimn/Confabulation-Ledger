# Architecture and policy contract (v0.1)

## Trust hierarchy

The **author** configures subjects, protected predicates, and scoped delegation. The **trusted simulator** supplies physical events and receipts through an in-process method. The **policy engine** may promote only a small allowlist of previously unspecified, low-impact facts from direct character dialogue when the speaker has authorized scope. The **character/extractor** supplies an untrusted candidate. The **observer** or **listener** may receive an attributed claim without authenticating its truth. No number of repeated claims counts as corroboration in v0.1.

**Important limitation:** owner and speaker identity are externally supplied, not authenticated by this local prototype. An integrating host must bind identity to an authenticated actor and must not expose `Ledger.record_world_event`, `Ledger.override`, or `Ledger.review` as model-callable tools.

## Append-only events

SQLite `events` has sequential `seq`, `event_type`, JSON `payload`, `recorded_at_utc` (timezone-qualified ISO 8601), and `swatch_beat` (UTC+1 time of day as `@000` through `@999`). The original natural-language text stays byte-for-byte within the submitted JSON string. Client-side `source_key` is a trace token, not evidence of independence.

Events used in the first prototype:

| Type | Payload purpose |
| --- | --- |
| `ENTITY_REGISTERED` | Stable subject, owner, protected predicates, delegations |
| `CLAIM_SUBMITTED` | Raw statement, structured proposition, source and narrative date |
| `CLAIM_DECIDED` | Automated status, policy version, explicit decision rationale |
| `CLAIM_REVIEWED` | Subsequent human status revision, never destructive edit |
| `WORLD_EVENT` | Trusted physical change with receipt and effective date |
| `EDITOR_OVERRIDE` | Authored continuity correction with rationale |
| `CLAIM_HEARD` | Attributed transmission of a claim to a listener |

Status is `CANON`, `BELIEF_ONLY`, `PENDING`, or `REJECTED`. In v0.1, `BELIEF_ONLY` means noncanonical *attributed speech*, not proof that the speaker sincerely believes the proposition. A future epistemic model must separate assertion, sincerity, and conviction.

## Adjudication precedence

Unknown subject or speaker, unresolved reference, and protected-predicate operations are never automatically promoted. Dream, book, hearsay, diary, narrated, or observed-source content submitted as character claims is noncanonical, regardless of its claimed confidence. Wishes, lies, jokes, questions, hypotheticals, and uncertain speech remain attributed. Higher-impact predicates remain pending; unfamiliar predicates are never assumed safe. A speaker may auto-promote an allowlisted attribute only when they own the subject or possess a specific predicate delegation. Existing canon blocks conflicting restatements; consistent repetition does not create evidence. Historical backfilling in the presence of any previously accepted or receipt-backed fact is held for review.

A real simulator may record a *new* physical fact using a receipt; that creates a temporal transition. The simulation must attest to the receipt. No natural-language sentence supplies one.

## Temporal projection

`canon_at(date, viewer)` is recomputed from the complete event stream. Only the latest decision for a claim controls inclusion. Candidate world facts are ordered by narrative effective date and event sequence, and the most recent as of the requested date wins per subject-predicate pair. A private fact is visible to the author/operator, its owning character, or the speaking character; no other observer receives it as canonical knowledge. This is sufficient for the seed example, **not** a complete valid-time interval or knowledge-time model.

The code presently does not model a character's knowledge acquisition date for shared public canon, so `character_view` should be read as *accessible canon*, not confirmed knowledge. Future versions must store knowledge receipt time, ignorance, secrecy, and allowed revelation paths. The experiment must also separate narrative valid time from knowledge time and system recording time.

## Threat model and limitations

The local HTTP interface binds to `127.0.0.1` and exposes only structured claim submission and read-only projections. It is not intended for public deployment, remote authentication, or multi-user access. Its basic browser-origin check is not an authorization mechanism. As currently implemented, an untrusted local caller can impersonate a speaker in the claim endpoint; this must be fixed by a real host identity layer before integration. It cannot invent trusted receipt events through that endpoint.

Policy version is an identifier attached to decisions; a future migration must preserve exact executable rule versions and rerun them on pinned transcripts. Reproducible research should preserve software revisions and seeded prompts. Time travel with conflicting backdated editorial revisions, cross-predicate logic, and actor-specific epistemic horizons all require additional formal treatment.
