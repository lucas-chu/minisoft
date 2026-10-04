# Minisoft: 100 useful workflow tools

Build one selected product on each hourly wake of the same Codex chat. Start with **#33 MiniHackathon**, then **#1–32**, then **#34–100**. A difficult product can span several wakes; 100 is the target number of accepted products, not a promise of 100 hours.

Workspace: `/Users/lucaschu/code/minisoft`. Each idea has a numbered folder in `apps/`. The original list is in [catalog/source-ideas.md](catalog/source-ideas.md) and the machine-readable queue is [catalog/ideas.json](catalog/ideas.json). Setup created folders with briefs only; read the live ledger for actual implementation progress.

## Start here

Read [AGENTS.md](AGENTS.md), then run:

```sh
cd /Users/lucaschu/code/minisoft
python3 scripts/factory.py status
python3 scripts/factory.py next
python3 scripts/factory.py validate
```

`state/progress.json` is authoritative for progress. `state/automation.json` records the actual schedule returned by Codex. `runs/` contains accepted release receipts. Do not maintain a second hand-edited completion count here.

## System map

| Layer | Purpose | Read when |
| --- | --- | --- |
| Source/catalog | Preserve 100 ideas and stable IDs | Selecting or interpreting a product |
| Control plane | Claim, prevent overlap, checkpoint, accept receipts | Every hourly run |
| Product contract | Define workflow, data, acceptance, limits | Before implementation |
| Shared packages | Reuse proven data, permissions, UI, imports, audit, recovery | A consumer needs the capability |
| Product module | Implement specialized behavior in its numbered folder | Building that product |
| Verification/release | Tie tested behavior to published source and URL | Before counting completion |
| Design feedback | Record proven patterns and changed contracts | At each accepted release |

Read [architecture](docs/architecture.md), [product contract](docs/product-contract.md), [runbook](docs/runbook.md), and [decisions](docs/decisions.md) for their linked contracts. Inspect the selected product and actual dependencies instead of scanning all 100 folders.

The heartbeat runs locally. Keep this computer awake and Codex running. It inherits this chat's model and available subagent slots. “Tokenmaxx” means productive parallelism and thorough verification; it does not bypass account limits or create an unlimited token budget.

## Release standard

An accepted product has a working primary workflow, appropriate persistence/export, meaningful checks, runtime evidence, an independent review, accurate instructions, and verified deployment when it has a website. Ordinary clicks should not require model calls. Missing credentials, broken core behavior, and failed publication leave work incomplete.

Website builds reuse the existing provider, site, audience, and domain. If none exists, prefer one private Minisoft hub with stable product paths using the available Sites workflow. Record real provider IDs after provisioning. A hub is a deployment preference, not a requirement to force native tools into a browser.

When all 100 products have accepted receipts, disable the heartbeat. Unchanged states stay quiet; releases, new actionable blockers, and completion receive concise updates.
