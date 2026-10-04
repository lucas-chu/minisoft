# Product contract and release evidence

Create `SPEC.md` before implementation. Preserve the original brief in `IDEA.md`; update its status pointer when work starts. Define a useful scope satisfying the idea without promising an entire enterprise suite.

## SPEC.md template

```markdown
# Product name (source ID)

## User and replaced workflow
User, expensive/manual workflow, concrete result.

## Useful first release
End-to-end behavior, deferred features, actual boundaries.
Tier: prototype / sandbox / operational; explain the basis.

## Inputs, outputs, and sample data
Formats, schemas, source evidence, fixtures, exports.

## Domain operations and invariants
IDs, validation, transitions, calculations, conflict behavior.

## Persistence and access
Storage scope, reload/restart, role enforcement, retention, recovery.

## Dependencies and shared capabilities
Actual packages/adapters, commands, credentials, failure behavior.

## Acceptance scenarios
Given/when/then for primary workflow, errors, persistence, exports,
calculations and permissions where promised.

## Verification and publication
Checks, runtime walkthrough, actual provider/site/audience/route.

## Limits and remaining prerequisites
Unsupported inputs and external review/approval required for real use.
```

## First product: MiniHackathon

Default to an organizer workspace configured from one brief, with synthetic participants/judges. Deliver event/rubric configuration, application capture/review, team formation, project submission records, judge assignments with conflicts, score capture, explainable results, and export. Applicant/judge self-service requires real identity, shared persistence, and access enforcement.

Explain weights, missing evaluations, ties, disqualification, and judge coverage. Test conflicts, invalid scores, team membership, incomplete scoring, weights, ties, persistence, and exports. Label samples. Do not contact real participants or collect private event data to test.

## Completion evidence

Receipts identify product/run, scope/tier, source identity, changed files, successful check commands, runtime evidence, persistence/export checks or justified non-applicability, independent review/resolution, actual limits, and publication when applicable. Use the exact schema accepted by `scripts/factory.py` and linked from the runbook.

A screenshot alone does not prove domain operations. Tests repeating implementation provide weak evidence. Missing credentials, broken primary workflows, placeholder core actions, and failed deployments leave work incomplete. Document optional future features without disguising missing required behavior.

High-consequence briefs require reviewed rules, approvals, external validation, or sandboxing. Preserve these in the product. A useful narrow sandbox can satisfy its first-release contract; external readiness remains a distinct status and cannot be inferred from the suite's completion count.
