# One system, many specialized workflows

The unit of value is a real completed workflow. The unit of implementation is a product module. The unit of trust is a release receipt tied to verified source and behavior. The unit of coordination is one claimed product per heartbeat. A directory does not establish completion.

## Linked abstractions

```text
source idea -> product contract -> domain operations -> storage/integration adapters
                              \-> human interface and agent-readable controls
                                   -> verification -> release -> accepted receipt
                                                         \-> shared design learning
heartbeat -> claim/resume -> one product -> checkpoint or accepted receipt -> next wake
```

The catalog owns identity/order. Progress owns mutable status and lease. `runs/` owns durable evidence. Product `SPEC.md` owns promised behavior; code/tests implement it. Product `README.md` owns use instructions and actual limits. Automation metadata points to the schedule managed by Codex. Other documents must not silently redefine these authorities.

The control plane uses Python's standard library with no model API or service dependency. It coordinates builds; it is not the product runtime. Choose and record the actual product stack during the first build based on workflow and deployment, then reuse compatible tooling.

## Shared foundation

Grow `packages/` from current requirements. Expected boundaries are typed records/validation, permissions, imports/exports, files, UI primitives, audit history, and recovery. These are design boundaries, not implemented-package claims.

Domain behavior is independent of UI and external providers. Calculations, assignments, reconciliations, and transitions must be callable as typed operations and tested without clicks. Side effects sit behind adapters with clear capabilities, configuration, failures, and justified retries. Storage declares local/shared persistence, transactions, and permission enforcement explicitly.

Each product owns specialized schemas and rules. Shared modules own proven reusable contracts. Reuse the substrate while preserving distinctive workflows; a generic table editor does not satisfy every idea.

## Agent legibility

Each product README exposes canonical development, check, build, export/recovery commands. Include fixtures, stable IDs, structured results, useful errors, and evidence links. Mutations identify target, expected version, side effects, and recovery. Handle conflicts and irreversible operations explicitly.

Inspect the selected product's contract, checkpoint, and dependencies before widening searches. Receipts prevent rediscovery of commands and deployment identities. Record unknowns as unknowns; imported notes and inferred fields cannot become fabricated authoritative records.

## Modular deployment

Prefer one hub with stable product routes and source in numbered folders. Share compatible platform services. Native extensions and heavy media/solver tools keep specialized build contracts; the hub can link verified artifacts.

After provisioning, record actual provider, remote if required, site ID, audience/domain, configuration names, and routing. Store secret values in provider secrets. Every edit uses that identity. Label unfinished modules accurately.

Receipts tie source revision/digest, deployed revision, deployment status/ID, and URL. A shared change requires verifying affected consumers. If it alters a released workflow, update docs, verify, and publish the affected site in the same run before accepting the selected product.

## Accretion without ambiguity

At each release, identify what the consumer proved: schema, adapter, fixture, UI primitive, error pattern, or validation technique. Extract when it reduces actual duplication. Record evidence, affected consumers, compatibility, and checks in decisions. Keep operating guidance compact; retain historical evidence in receipts.

Measure accepted workflows and reusable tested capabilities. Separate total runs, incomplete work, blockers, publication state, and unique products. Multiple wakes on a complex product are legitimate; duplicate completion and unsupported production claims are not.
