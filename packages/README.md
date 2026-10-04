# Shared capabilities

No runtime packages are implemented yet. Add the smallest capability required by the current consumer and document operations, inputs/outputs, invariants, persistence/access, consumers, and checks. Extract repeated behavior when real consumers establish the contract.

Expected boundaries: records/validation, UI, permissions, import/export, files, audit, recovery, and storage/compute/integration adapters. Avoid prebuilding them all or forcing specialized media, extensions, solvers, and ledgers into generic CRUD.
