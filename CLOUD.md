# Cloud cutover contract

The user explicitly requested moving this hourly series to the cloud so it can run without the Mac. The former local heartbeat `minisoft-hourly-builder` is paused and preserved in `state/local-automation.json`. Do not reactivate it from a cloud run or use its ID to manage the cloud schedule.

This file supersedes environment-specific Mac assumptions in the original local heartbeat prompt. Preserve the source IDs/order, one product per wake, acceptance rules, permission boundaries, and website publication obligations in AGENTS.md.

## Bootstrap before activation

Import the supplied private archive once into the actual cloud workspace. Verify its outer SHA-256 and file manifest before running its scripts. The seed has 100 unique ideas, 0 accepted products, no active lease, and MiniHackathon #33 next. Run `python3 scripts/factory.py validate`, `status`, `next`, and `python3 -m unittest discover -s tests -v`. At transfer, the control plane has 14 passing tests.

Record the real cloud workspace root, cloud chat/task ID, runtime, persistence model, storage identity, and scheduler management tools in `state/cloud.json`. Adapt available browser/publishing tools and subagent capacity to the cloud environment. The standard-library factory script already derives its root and stores relative evidence paths.

## Verify durability

Determine whether hourly wakes resume this task's durable filesystem. If they do, create a persistence marker and verify it on a subsequent resumed turn before activating the repeating schedule. If wakes use fresh containers, restore the newest authoritative cloud checkpoint and save a new version after each run using an actual durable store with conflict detection. Never repeatedly re-extract the original empty seed. Keep a single builder identity; the filesystem lease cannot coordinate separate independently restored containers.

Use a private repository or supported persistent cloud workspace as the preferred mutable code/state store. The private bootstrap archive is a transfer artifact, not automatically the live ledger. If using versioned checkpoint archives, record version, digest, accepted count and latest checkpoint reference, and prove serialization before enabling the schedule. Do not overwrite another worker's newer state.

## Activate one hourly cloud heartbeat

Configure a native cloud schedule that returns to the same cloud series task if supported. Use the saved cloud heartbeat prompt and available scheduler tools. Do not create a local scheduled task, desktop-dependent process, unmanaged background sleep loop, or a second series builder. Preserve hourly cadence and one selected/resumed product per wake.

Save the actual cloud scheduler ID and verified active status in `state/automation.json`. The actual cloud management tool replaces the old local tool in the stop-at-100 procedure. If scheduling or durable continuity cannot be established, leave the cloud schedule inactive and report the precise blocker rather than claiming the migration is complete.

Report cloud cutover evidence: imported checksum/catalog status, tests, actual runtime/workspace, persistence proof across turns or restores, scheduler ID/status/cadence, local schedule PAUSED, and the first queued product. Preserve release tiers, immutable receipts/evidence, and existing provider identities through future updates.
