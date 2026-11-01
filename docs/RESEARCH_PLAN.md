# Confabulation Ledger: Research Plan

**Working title:** Controlled Canon Formation Through Generative Character Claims  
**Date:** November 2026  
**Status:** Proposed research; deterministic laboratory scaffold implemented, empirical hypotheses untested.

## Abstract

In persistent, AI-mediated fiction, a statement that is not present in the world's established canon is not necessarily an error. It might be a legitimate act of invention. The Confabulation Ledger investigates a governed transition by which eligible character assertions become authoritative fictional facts while contradictory, uncertain, private, hypothetical, or unauthorized statements remain attributable to speakers. It preserves original utterances, decision provenance, temporal boundaries, and reversible edits. Success must be evaluated against creative yield, continuity violations, character-specific belief consistency, and human authorial control.

## Research questions

The primary question is whether a selective, reversible canonization policy increases meaningful detail creation and subsequent correct reuse compared with a closed-canon baseline, without increasing violations of protected world facts. A second question is whether separating shared world state from individually attributed claims allows stable disagreement and unreliable memories. A third concerns authority: which policies balance improvisational character agency with the rights of the author, game master, and players? A fourth asks whether complete provenance improves the recovery and diagnosis of mistakes.

These are hypotheses, not findings. The present prototype exercises individual policy decisions but does **not** validate these research claims.

## Operational distinctions

A **candidate claim** is an atomic proposition extracted from situated utterance. A **decision** is an adjudication of that proposition under a named policy. **Canon** is the time-indexed authoritative world projection after accepted claims and trusted events. A **character view** includes visible canon and attributed claims, distinguishing direct statement, reported hearsay, uncertain interpretation, and received rumor. **Provenance** is immutable event evidence, not a confidence label.

An utterance such as "My wife has yellow hair" may introduce an open low-impact attribute where the speaker has delegated authority. "I heard the mayor owns a dragon" does not prove that dragons exist; a diary dream does not establish witnessed action; a character claiming to have bought coal does not fabricate the inventory event required for a successful purchase.

## Core experimental conditions

Compare a model with no persistent factual memory; a restrictive read-only canon; an unrestricted accept-and-store baseline; and a governed ledger. Use matched seed worlds, model and token budgets, dialogue scripts where applicable, and multiple stochastic runs. Distinguish extraction errors from adjudication errors and downstream generation failures. The deterministic benchmark should run without an LLM, and the generative study should evaluate the full extraction/generation pipeline separately.

Suggested metrics include protected-canon violation rate, precision of new fact promotion, useful creative reuse, retrieval accuracy across simulated time, provenance completeness, reversible error recovery, character-specific disagreement consistency, annotation agreement, and cost. Independent judges should be blinded to experimental condition where feasible. Prespecify a meaningful creative-reuse threshold and a maximum acceptable protected-canon violation rate before formal trials; avoid inventing post-hoc success thresholds.

## Benchmark taxonomy

Build micro-world scenarios with intentionally open attributes; fixed creator lore; protected facts; ambiguous reference; temporal change backed by a simulation receipt; unsupported off-screen action; quoted, joking, hypothetical, or sarcastic speech; intentional deception; misremembered personal history; confabulation of another character's biography; rumor cascades; repeated self-corroboration; private information; retroactive revision; restart and delayed-recall tests.

Each benchmark example needs the original utterance, typed entities, narrative date, prior world state, actor authority, expected disposition, evidence requirements, and an independent rationale. Include negative controls and ambiguous cases that should remain pending, not mechanically become true or false.

## Prototype sequence

**Phase 1, deterministic laboratory:** define the ontology, low-impact predicate allowlist, authority delegation, source modality, event log, reversible status, temporal projection, and a seed corpus. Implement API and local dashboard. Require tests to pass without calls to language models. **This phase is partially implemented.**

**Phase 2, controlled generation:** add interchangeable language-model extractors through a strict structured-output contract, track raw transcript offsets, freeze model versions and prompts, and reject unresolved references. Never let generated prose invoke trusted simulation receipts or editorial overrides.

**Phase 3, comparative evaluation:** assemble seed worlds and annotation protocol, run the four experimental conditions, blind independent evaluators where possible, and publish both negative and positive outcomes with reproducible costs.

**Phase 4, optional external validation:** integrate through a narrow adapter with a persistent fictional village. Keep ownership of the authoritative world and physical action receipts with the host simulator, not with the ledger's language model.

## Risks and governance

A missing fact does not imply authority to invent it. The system must prevent canon contamination, unauthorized invention of player biographies, fabricated material consequences, accidental disclosure of private information, and self-reinforcing evidence loops. Treat fictional canon as distinct from empirical truth. Human overrides must be explicitly attributed, not silently edited. When policies conflict, a pending decision is scientifically preferable to a convenient hallucinated certainty.

## Prior work and scope of novelty

This proposal draws on simulation memory, truth maintenance, and point-in-time narrative consistency. Novelty is **not** claimed for memory storage, belief graphs, or contradiction detection separately. The proposed contribution is an explicitly governed and evaluated *promotion operation* that tests the tradeoff between emergent worldbuilding and canon preservation.

- Park, J. S., et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* UIST. https://doi.org/10.1145/3586183.3606763
- Landwehr, F., Varis Doggett, E., & Weber, R. M. (2023). *Memories for Virtual AI Characters.* INLG. https://aclanthology.org/2023.inlg-main.17/
- Doyle, J. (1979). *A Truth Maintenance System.* Artificial Intelligence, 12(3), 231-272. https://doi.org/10.1016/0004-3702(79)90008-0
- Ahn, J., et al. (2024). *TimeChara: Evaluating Point-in-Time Character Hallucination of Role-Playing Large Language Models.* Findings of ACL. https://aclanthology.org/2024.findings-acl.197/
- Tian, Q., et al. (2026). *Shared Worlds, Private Minds: Structured Memory for Long-Form Writing as World Creation.* arXiv. https://arxiv.org/abs/2609.32401

A broad independent novelty and prior-art review remains necessary before publication.
