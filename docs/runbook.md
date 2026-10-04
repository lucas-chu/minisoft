# Hourly build runbook

## Orient and select

Work in the Minisoft workspace root. Read `AGENTS.md`, run `status` and `next`, then inspect the selected product/dependencies. Selection begins with #33, then the remaining list in order.

If `next` returns no eligible product while completion is below 100, inspect recorded blocked prerequisites cheaply. Unblock only when evidence shows a prerequisite changed; otherwise stay quiet. An empty eligible queue is not series completion.

Use `python3 scripts/factory.py --help` and subcommand help for exact flags. The coordinator claims the product with its actual identifier and saves the returned run ID. Children do not edit state. A filesystem mutex protects writes; a durable lease prevents concurrent builds.

An active lease means skip quietly. Before explicit expired-lease recovery, inspect previous coordinator/children/processes and confirm they stopped. If active, do not steal the lease. Renew it during long work. Stop/join children before releasing it.

## Plan and delegate

Write/refresh `SPEC.md` from the product-contract template. With four slots, use up to three children for domain/data, UI/workflows, and independent verification. Give disjoint ownership and concrete acceptance/evidence requirements. Use fewer for small tasks; record the choice. The coordinator owns integration, shared contracts, state, and publication.

Reserve time for checks, runtime walkthrough, and release. Aim to checkpoint within 50 minutes before the next hourly wake; renew if legitimately continuing. Cadence initiates work, not guaranteed completion within an hour. Keep the acceptance standard.

## Build and verify

Implement the real primary workflow using proven shared capabilities. Ordinary operations remain deterministic. Expose missing integration configuration accurately. Keep credentials and private records out of samples/evidence.

Exercise actual UI/runtime from input to usable output. Verify relevant error paths, calculations, persistence, permissions, and export/recovery. An independent reviewer inspects the implemented contract and reports concrete findings. Fix material findings and recheck affected behavior.

## Publish and accept

Read hosting metadata before creating/changing a provider. If none exists, use Sites building/hosting skills where appropriate and prefer one private suite hub. Persist real IDs/routes. Reuse provider/site/audience/domain thereafter.

Publish exact verified source. Verify terminal success and expected served revision. If blocked, preserve local work and record what remains unpublished; local checks cannot substitute for required deployment.

Update product docs, record the receipt schema from `scripts/factory.py`, and accept using `complete --run <actual-id> --receipt <actual-path>`. Start with [receipt.example.json](receipt.example.json) and replace every placeholder with actual evidence; the example itself is not acceptable evidence. `digest --files <exact changed_files list>` computes the source digest after final edits. Keep exact commands, evidence references, source identity, reviewer resolution, limits, and deployment evidence. Accepted evidence is copied into `runs/`. Record proven reusable learning in decisions and update affected design contracts.

Stop after this product. Report releases/new actionable blockers concisely; unchanged blockers and skipped overlap stay quiet.

## Checkpoint and recovery

Before yielding unfinished work, preserve changed files, contract, checks, blockers, and exact next steps using `checkpoint --run <id> --note <continuation>`. External prerequisites can use the blocked option; blocked work retains its identity without counting as complete. Stop/join children before releasing the lease. Do not retry unchanged prerequisites indefinitely.

When a prerequisite changes, `unblock <source-id> --note <what changed>` makes it eligible again. Run `validate` after recovery/control-plane edits. Never repair corruption with fabricated receipts or counts.

## Finish the series

At 100 accepted products and no unfinished work, find the existing heartbeat in `state/automation.json` and disable it through its actual scheduler management tool, preserving other fields. Verify the returned inactive/paused state and save it. If disabling fails, future wakes do no product work and retry disabling. Report the final product index once. Do not archive this chat or impose a fixed 100-invocation cutoff.
