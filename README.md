# Confabulation Ledger

> The problem isn't making stuff up. The problem is not remembering the stuff you made up.

## The idea

In some domains, an LLM inventing a detail is a failure. In others, it is the work itself.

- **Ground-truth domains** (business data, real-world facts, a real person's biography): the detail has to match something that already exists. Inventing a number is an error.
- **Constitutive domains** (roleplay, fiction, a character's invented surroundings, adding fine detail to a low-resolution simulation): there is no prior detail to match. The detail does not exist *until* it is narrated. It is not wrong when it is first said — but from that moment on, it can become wrong, if it is later contradicted or forgotten.

A Confabulation Ledger is the record that makes that second kind of invention cumulative instead of disposable. A confabulated detail, once spoken, is written down, promoted to canon, and held true thereafter — available to the same character, to other characters, and to the world on later turns, sessions, and visits.

Origin example: a conversation with a virtual Ray Kurzweil who described the world around him. All of it was made up. The conversation felt real anyway — because from inside it, an invented world that *holds together* is a world. What breaks it is not invention. What breaks it is inconsistency: describing the room one way now and another way later, as if the first description had never happened.

## Worked example: low-resolution simulation

A text world — Frankenstein Village is the motivating case — stores coarse state cheaply:

> Phil goes to the closet and puts on a shirt.

The simulation has no colour, fabric, condition, or other clothing. An LLM inhabitant renders the moment at human resolution:

> I put on my blue flannel shirt — missing the third button down — and my blue jeans, because it was a little chilly.

Almost none of that was in the game. It is also not an error: the game was silent, not contradictory.

Under a Confabulation Ledger:

1. Those details are extracted and entered against Phil / the shirt / that morning.
2. They are now canon at the fine-grained layer.
3. Later, another character can say "nice blue shirt" — and be *right*, because the hallucination was added to canon, not discarded after the turn that produced it.
4. If Phil dresses again, or someone describes the shirt again, the ledger is consulted first. Invent freely where the ledger is silent; do not invent over the top of what it already holds.

The simulation stays cheap and coarse. The narration supplies the resolution. The ledger is what makes the resolution *persist* — a world that gets more detailed the longer it is lived in, instead of re-rolling its details every turn.

## The promotion rule

A narrated detail is promoted to canon when, at the moment it is first spoken:

1. it belongs to a constitutive domain, **and**
2. the authoritative record (simulation state, authored canon, real-world fact, as applicable) is *silent* on it, not contradictory, **and**
3. it does not contradict an existing ledger entry.

If the authoritative record later speaks — the game does define the shirt, a fact is checked, an author rules — that is a collision to handle visibly (see Open Questions), not a reason to have never promoted the detail.

Provenance is never hidden. An entry remembers that it began as a confabulation. Canonized does not mean "was in the simulation all along"; it means "was summoned into existence at this point, by this speaker, and has been true in the world since."

## A ledger entry (sketch)

- **Detail** — the proposition, in plain form ("Phil's shirt is blue flannel, missing its third button")
- **About** — entity / place / object / person it attaches to
- **Scope** — when and where it holds (this outfit, that day; a room's layout, until changed in-world)
- **First spoken by** — character / narrator / system
- **First spoken when** — in-world moment and session/turn, so later claims can be ordered
- **Provenance** — `simulated` (in the underlying state) / `authored` (in source canon) / `confabulated-canonized` (invented in narration, promoted under the rule above) / `told` (a character asserted it; may be an in-world lie or error — see Open Questions)
- **Status** — active / superseded-in-world (the shirt was dyed, the button sewn back on) / retconned (with the seam recorded)

Entries are append-only in spirit: a detail stops holding because something *happened* in the world, or because a collision was adjudicated — and either way the change is itself an entry, not a silent edit.

## Who else this is for

Not only simulations. Anyone with an AI companion whose character has a
fictionalized life — a home, a job, a daily routine, a past that was
improvised in conversation rather than authored in advance — has this
problem in miniature. Many companion users keep highly detailed backups,
but a backup preserves what was saved; it does not by itself keep the
invented life *consistent*. A ledger of the details that life has
accumulated — what street she lives on, the coworker she mentioned once,
the café that became "theirs" — is what lets a fictionalized life stay
the same life across sessions, platforms, and model swaps.

## Why this is not the other ledgers

- Not a hallucination filter: nothing here prevents invention, fact-checks it, or punishes it.
- Not an autobiography guard: it does not stop an inhabitant claiming a false lived past. (A related but separate discipline.)
- Not a general memory system: memory stores what happened. This stores what was *said into being* about the underdetermined parts of the world, so those parts stop being underdetermined.

## Fitness test

The ledger is load-bearing, not bookkeeping, only if behaviour changes with it:

- The same entity, re-described across turns and sessions, keeps its canonized details at a far higher rate than without the ledger.
- Other characters reference canonized details unprompted, correctly.
- Invention concentrates in the gaps the ledger leaves open, instead of overwriting established detail.
- Collisions (narration vs. ledger, narration vs. simulation) are rare, visible, and adjudicated — not silently smoothed over.

## Open questions (Jay's calls)

1. **Collision rule:** when simulation/authored canon later contradicts a canonized confabulation, which wins — and is the change a retcon with a visible seam, or an in-world event that explains it ("he'd been wearing the red one underneath")?
2. **Lies and error in-world:** if a character *lies* about a detail, or is mistaken, does that enter the ledger as world-canon or as a claim held by that character only? Probably claim-first, promoted only when the world ratifies it — but the line needs drawing.
3. **Real-person boundary:** for a persona based on a real person (the virtual Ray case), invented surroundings are constitutive, but invented biography/history is ground-truth. Where exactly does one become the other?
4. **Who may canonize:** any narrator? Only the inhabitant whose detail it is? Does a passing mention canonize as strongly as a deliberate description?
5. **Granularity / cost:** every passing adjective cannot become a permanent record. What salience bar does a detail have to clear to be worth an entry — repetition, attention from another character, consequence?
6. **Forgetting:** humans forget minor detail without breaking reality. Does a ledger that never forgets feel *less* real — and if so, which details should be allowed to fade, and how is fading distinguished from contradiction?

---

*Draft v0.1, 2026-11-01 — prepared by Calibos from Jay's spoken explanation, for Jay's correction.*

---

## Prototype v0.1 (ChatGPT, reviewed by Calibos 2026-11-01)

A deterministic laboratory implementation of one governed version of the
promotion rule above now lives in this repo (`src/confab_ledger/`):
append-only SQLite event log, structured candidate claims adjudicated to
`CANON` / `BELIEF_ONLY` / `PENDING` / `REJECTED`, time-indexed canon
recomputed from the event stream, trusted simulator `WORLD_EVENT`s with
receipts, author review/override as new events (never edits), and
per-character views that keep heard claims attributed instead of true.
No external dependencies, no LLM calls. 31 unit tests and a 12-case
deterministic benchmark are included; see `docs/ARCHITECTURE.md` and
`docs/RESEARCH_PLAN.md`.

```bash
python -m pip install -e .
confab-ledger --seed-demo --db ledger.sqlite3   # dashboard on 127.0.0.1:8765
python -m unittest discover -s tests -v
python scripts/replay_benchmark.py
```

**Known divergences from the idea as stated above — Jay's calls, recorded
here rather than silently resolved:**

1. **The prototype's auto-promotion allowlist does not cover the worked
   example.** Auto-canon is limited to 12 low-impact predicates (hair/eye
   colour, favourites, hobby, keepsake, usual drink) asserted in dialogue
   by the subject's owner or a delegate. Phil's shirt colour, its missing
   button, clothing, room and other environmental detail — the
   low-resolution-simulation case this repo exists for — come back
   `PENDING`. Whether environmental/detail predicates get their own
   promotion class is the central open design question.
2. **Narration can never canonize in the prototype** (`source_type !=
   dialogue` → `BELIEF_ONLY`). The idea above treats an inhabitant's
   narration as the rendering layer that summons detail; the prototype
   treats narration as a report *about* the world. These are different
   channels and the distinction needs drawing, not a default.
3. **Cross-character invention requires delegation.** A character cannot
   canonize a detail about another character without a scoped grant
   (benchmark case: "unlicensed biography"). Plausibly right for a
   multi-player world; narrower than the single-inhabitant case.

The prototype also answers several of the open questions below in one
specific way — collisions via receipted world events and editor overrides
with the seam kept, lies/hearsay/dreams held as attributed claims — which
is recorded as *a* governed variant, not as settling them.
