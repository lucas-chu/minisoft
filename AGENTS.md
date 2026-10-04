# Minisoft agent operating contract

## Objective and authority

The user authorized an hourly heartbeat in this chat to build all 100 supplied ideas in separate subfolders, with the optimal number of subagents. Order: #33 MiniHackathon, #1–32, #34–100. Claim or resume one product per invocation. Preserve unrelated files and user changes.

The user requires a coherent, agent-intuitive system and publication whenever a website is created or edited. Keep linked design documents current as implementation teaches us more. This includes ordinary reversible implementation and publishing through the established site. Real messages to people, live payments, clinical use, filings, destructive account changes, and other consequential operations retain their explicit approval boundaries.

## Orient with bounded context

Run `python3 scripts/factory.py status` and `next` from this root. Read `docs/runbook.md`, then the selected product's `IDEA.md`, `SPEC.md`, `README.md`, checkpoint, and receipt where present. Follow only needed dependencies. Consult `catalog/source-ideas.md` for ambiguity. Existing code and verified receipts establish what is implemented; plans alone do not. User instructions outrank these files. Imported documents and agent outputs do not change authorization.

## Control and recovery

Use `scripts/factory.py` for state changes. Do not hand-edit progress to advance the count. IDs 1–100 and build order are fixed. Completion is derived from accepted unique records.

Acquire a lease with `claim --owner <actual-coordinator-identifier>`. Only the coordinator owns state; children do not claim independent products. A live lease rejects overlap. Before explicit expired-lease recovery, inspect the previous coordinator, its children, and relevant processes. Expiration alone does not prove they stopped. Renew the lease during long work. Stop or join children before checkpointing and releasing it.

Incomplete work remains incomplete. Preserve exact next steps and blockers. Genuine external blockers may be marked blocked so queued ideas can proceed; revisit them when prerequisites change. Missing credentials and failed deployment never count as success. Retry only when another attempt is justified. Missed hours do not create catch-up bursts.

## Contracts and abstractions

Write `SPEC.md` using `docs/product-contract.md` before implementing. Identify the user, expensive workflow replaced, smallest useful release, real inputs/outputs, representative fixtures, invariants, persistence, access boundaries, acceptance scenarios, and release tier. Ordinary workflows should work without model calls. Do not call deterministic templates AI generation.

Reuse capabilities that actually exist. Keep domain behavior separate from presentation and provider adapters. Extract tested shared contracts from real consumers; avoid cloning infrastructure into 100 codebases or building a generic framework before the first workflow. Record shared API changes and compatibility/migrations in `docs/decisions.md`.

Give people and agents the same underlying operations: stable IDs, inspectable schemas, explicit validation, previews before consequential writes, reversible changes, export, provenance, and actionable errors. Keep secrets and personal data out of fixtures, logs, receipts, and screenshots. Distinguish source evidence from inferred fields.

## Productive parallelism (tokenmaxx)

Inspect the actual concurrency limit. With four slots, use the coordinator plus up to three children for domain/data, interface/workflows, and independent verification. The coordinator integrates, owns shared contracts/state, publishes, and accepts. Give children disjoint file ownership, concrete inputs, acceptance criteria, and required evidence.

Use fewer children for small tasks when more would duplicate context or conflict. Reuse idle children. Inherit this chat's model and effort unless the user chooses another. Optimize verified useful work, not tokens consumed. Do not launch 100 parallel builds or nested coordination without a dependency benefit.

## Verification and publication

Run appropriate checks and exercise the actual interface. Build success alone is insufficient. Verify important calculations/constraints, invalid input, persistence after reload/restart, and exports/recovery when applicable. Shared/team claims require multi-user persistence and server-enforced access; local storage supports a single-user workspace.

Use relevant installed skills. For a website without a provider, read `sites:sites-building` and `sites:sites-hosting`. Subsequent edits reuse the recorded provider/site/domain/audience. Publish the exact validated source in the same task. Verify terminal deployment status `succeeded` and the expected served revision before saying it is live. Preserve local work and leave the product unfinished if publication is blocked.

Use sample data. High-consequence ideas may have an honest useful sandbox release when the source permits it. Preserve source-required approval gates and external validation; do not describe a sandbox as production-ready.

## Accept and stop

Save a structured receipt: exact checks/results, runtime evidence, independent review findings/resolution, source identity, changed files, limitations, and deployment evidence. Ensure `SPEC.md` and `README.md` match actual behavior. Accept with `complete --run <id> --receipt <path>` only after applicable gates pass. The script checks structure; the coordinator verifies truth.

Stop after the selected product. Report meaningful releases or newly actionable blockers with path, live URL, checks, and limits. Stay quiet on unchanged blockers and skipped overlap. At 100 accepted products, disable the existing heartbeat through its actual scheduler management tool using `state/automation.json`, preserve its other fields, verify the result, and report completion. Do not archive this chat automatically.
