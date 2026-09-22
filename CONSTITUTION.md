# CONSTITUTION — Strategy-Based Task Scheduling & Resource Limitation System

**Status:** Authoritative. Ratified by the Tech Lead.
**Scope:** This document governs ALL code generated for this repository.
**Normative keywords:** `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `NEVER`.
`MUST`/`NEVER` are hard constraints; violations are rejected. `SHOULD` requires justification before deviating.
**Language-agnostic:** Rules are expressed independent of any programming language. The concrete implementation language MUST respect these rules in their idiomatic form.

---

## 1. Preamble & Scope

1.1. This constitution is the single source of truth for architectural and quality decisions. Any prompt, suggestion, or AI-generated code that conflicts with it MUST be rejected.

1.2. The purpose is to produce a maintainable, extensible, testable refactor of the legacy prototype (see guidence.md) into a modular backend service.

1.3. Every contribution MUST be verifiable against the Definition of Done (Section 11).

1.4. AI agents MUST read this document before generating any code and MUST use it as the checklist during self-review.

---

## 2. Business Context & Domain Vocabulary

The system receives user-submitted task strategies, executes matching ones on a daily schedule, and limits each user's daily resource quota.

| Term | Definition |
| --- | --- |
| **User** | An identity that owns a daily execution quota. |
| **Quota** | Maximum number of task executions allowed for a user **per day**. |
| **Task** | A submitted strategy: `{ user, time, action, target, params? }`. |
| **Action** | The operation a task performs (e.g. `sync`, `backup`, `delete`). Actions are extensible strategies. |
| **Scheduler** | Matches tasks to the current time and triggers execution. |
| **Executor / Runner** | Executes an action while enforcing quota and logging. |
| **Execution outcome** | One of: `executed`, `time_miss`, `quota_exceeded`, `failed`. |

---

## 3. Domain Invariants (Business Rules — MUST)

3.1. **Quota is per-user and per-day.** The executed counter MUST reset on a new day. A daily rollover mechanism is mandatory.

3.2. **A single user MAY have multiple tasks at the same time.** Each task is evaluated and counted independently.

3.3. **Quota enforcement:** A task whose user has reached quota MUST be **skipped** and logged as `quota_exceeded`. It MUST NOT be partially executed and MUST NOT raise an application error.

3.4. **Quota check consistency:** The eligibility check MUST be defined exactly once and reused by every execution path (DRY core nod).

3.5. **A task is eligible if `executed < quota` at evaluation time.** After an execution, the counter for that day MUST be incremented atomically with respect to the decision — no gap between "allowed" and "counted".

3.6. **Clock MUST be injectable.** The scheduler MUST NOT call the system time directly; it MUST consume a clock/time-provider dependency so scheduling logic is deterministic in tests.

3.7. **Task configuration MUST be supplied externally** (e.g. dictionary input), validated at the boundary, and never hard-coded inside domain or use-case modules.

3.8. Each task execution MUST produce a traceable log line (see Section 8).

---

## 4. Core Engineering Principles

### 4.1. SOLID

- **S — Single Responsibility:** Each module/class MUST have exactly one reason to change. A module MUST NOT mix model, rule, I/O, and wiring concerns.
- **O — Open/Closed:** The system MUST be extensible to new action types WITHOUT modifying existing executor/scheduler behavior. Extension via strategy + registration; NEVER via editing a dispatch `if/switch`.
- **L — Liskov Substitution:** Every Action strategy MUST honor the execution contract (same outcomes, same logging semantics, same quota behavior). A strategy MUST NOT silently weaken invariants.
- **I — Interface Segregation:** Dependencies MUST be expressed as narrow, role-focused interfaces (e.g. "scheduling receiver" vs. "quota checker"). No consumer SHOULD depend on methods it does not use.
- **D — Dependency Inversion:** High-level modules (scheduler, executor) MUST depend on abstractions, not concrete implementations. Concrete wiring occurs only in the composition root.

### 4.2. Modularity

- Modules MUST have clear, single-direction dependencies. **Circular dependencies are prohibited.**
- Modules MUST expose a minimal public surface; internal details MUST be hidden.
- A module SHOULD be independently testable.

### 4.3. Don't Repeat Yourself (DRY)

- Each piece of knowledge/business rule MUST exist in exactly one authoritative place.
- Quota eligibility, outcome/log formatting, and config validation MUST NOT be duplicated.
- Repetition caused by language verbosity MAY be tolerated; repetition of **logic/rules** MUST NOT.

### 4.4. Separation of Concerns

- The following concerns MUST be separated into distinct layers: domain models, business rules, infrastructure (scheduling, I/O, time, logging), composition/wiring.
- Model code MUST NOT perform I/O or scheduling. Infrastructure code MUST NOT contain business rules.
- The composition root is the ONLY place where concrete objects are constructed and injected.

---

## 5. Architecture Blueprint (Mandatory Layering)

Dependency direction is **strictly one-way**:

```
    composition root
           │ (wires everything)
           ▼
    infrastructure / adapters   (scheduler, clock, config loader, logging gateway)
           │
           ▼
    use cases / application     (quota enforcement, task executor)
           │
           ▼
    domain                      (User, Task, Action strategy contracts) — pure, no I/O
```

- **domain:** Entities, value objects, strategy interfaces, domain rules. MUST NOT import infrastructure.
- **use cases:** Orchestration of domain rules against injected collaborators.
- **infrastructure:** Concrete time provider, scheduler loop, config parsing/validation, logging adapter.
- **composition root:** Reads config, builds and injects concrete dependencies, starts the system. MUST contain no business logic.

Rules:
5.1. Lower layers MUST NOT know about higher layers.
5.2. Namespace/file naming MUST mirror layers (e.g. `domain/`, `usecase/`, `infrastructure/` or equivalent in the implementation language).
5.3. The scheduler SHOULD be a simple loop with an injected clock for the initial implementation; async variants MUST reuse the same domain and use-case layers.

---

## 6. Extensibility Service (Open/Closed Enforcement)

6.1. Adding a new action type MUST be achievable by:
   1. Creating a new strategy implementation of the action contract;
   2. Registering it in a registry/factory (one line).
6.2. The executor and scheduler MUST NOT be edited to add a new action.
6.3. The action contract MUST define: validate params, execute with context (`user`, `target`, `params`), and return/log an outcome.
6.4. Params for each action MUST be validated inside that action's strategy (configurable via dictionary at the boundary).

---

## 7. Coding Conventions

7.1. **No global mutable state.** All shared state MUST be encapsulated and dependency-injected. In particular, user quota state MUST NOT be a module-global mutable dictionary (as in the legacy prototype).
7.2. **Explicit dependency handling:** Dependencies MUST be passed in (constructor/parameter injection); service locating or global singletons are prohibited.
7.3. **Config validation at boundary:** External input (e.g. task dictionaries, user definitions) MUST be validated immediately upon entry; invalid data MUST be rejected with a clear message, not silently coerced.
7.4. **Naming:** expressive and intention-revealing; action strategies SHOULD be named `<Action>Strategy` (or idiomatic equivalent). Functions/methods SHOULD be small and do one thing.
7.5. **Public boundary documentation:** Layer/module public entry points MUST be documented; internal helpers MAY be left undocumented.
7.6. **Immutable where possible:** Task definitions and user records SHOULD be immutable value objects once constructed.
7.7. **Fail fast, fail clearly:** Invalid state MUST raise a clear, typed error at the point of detection.

---

## 8. Error Handling & Logging

8.1. The system MUST use a proper logging facility (the language's `logging` module or equivalent). MUST NOT use print-to-stdout for operational logging.

8.2. Every execution path MUST produce a structured, traceable log line containing: user, task/id, action, target, outcome, and a reason on non-success.

8.3. Outcome taxonomy:
- `executed` → log info with details.
- `time_miss` → no execution, SHOULD be suppressed/debug level (normal behavior).
- `quota_exceeded` → log with user + quota + current count. Treated as a **business outcome**, not an exception.
- `failed` → log error with full context (user, task, action, exception), MUST NOT crash the scheduler loop.

8.4. The scheduler MUST catch unexpected failures at the per-task boundary so one failing task cannot stop the remaining tasks.

8.5. The number of exception types MUST be small and domain-meaningful (e.g. `TaskValidationError`, `UnknownActionError`). Generic `Exception` swallowing is prohibited.

---

## 9. Testing Standards

9.1. Every module/layer MUST have unit tests (where the language supports it).
9.2. **Determinism:** Scheduler tests MUST use a fake/injected clock. Tests MUST NOT depend on the real wall-clock or on `sleep`.
9.3. Mandatory test cases:
- **Quota boundary:** zero quota; `executed == quota` (skip); `executed == quota - 1` (execute); user under quota.
- **Daily rollover:** counter resets on a new day.
- **Simultaneous tasks:** one user with multiple tasks at the same time — each evaluated (and counted) independently, stopping at quota.
- **Extensibility:** adding a new action strategy does not require modifying executor or scheduler (test via a stub strategy).
- **Config validation:** invalid task dict is rejected with a clear error.
- **Error isolation:** a failing action does not abort sibling tasks.
9.4. Tests MUST verify outcomes (logs/return values/counters), not implementation details, unless the detail is a mandated rule.

---

## 10. Prohibited Practices (NEVER)

| # | Prohibited practice | Why |
| --- | --- | --- |
| 1 | Module-global mutable collections holding user/task state | Violates 3.1/7.1; untestable, non-reset quota bug |
| 2 | Editing executor/scheduler dispatch to add a new action | Violates OCP (6.2) |
| 3 | Duplicating the quota eligibility check | Violates DRY (4.3) |
| 4 | Calling system time directly inside logic under test (hidden clock) | Violates 3.6/9.2 |
| 5 | Using print for operational logging | Violates 8.1 |
| 6 | Silent exception swallowing (`except: pass` or bare-catch) | Violates 8.5 |
| 7 | Circular dependencies between modules | Violates 5.1 |
| 8 | Business rules embedded in infrastructure or composition root | Violates 4.4 |
| 9 | Hard-coding task/user definitions inside domain/use-case modules | Violates 3.7 |
| 10 | Copy-pasting config validation or outcome handling | Violates DRY |

---

## 11. Definition of Done (DoD)

Before any code is accepted, ALL of the following MUST hold:

- [ ] No `MUST`/`NEVER` rule of this constitution is violated.
- [ ] All `SHOULD` deviations are documented and justified.
- [ ] Modules respect the layering in Section 5; dependency graph is acyclic.
- [ ] Quota logic exists exactly once (DRY) and enforces per-day semantics + atomic check/increment.
- [ ] Clock is injected; scheduler tests are deterministic.
- [ ] Every execution path logs a traceable outcome (8.2/8.3).
- [ ] Mandated test cases (9.3) exist and pass.
- [ ] New action types can be added without touching executor/scheduler.
- [ ] Code is named clearly, config validated at boundary, no global mutable state.
- [ ] Self-review note recorded explaining how the implementation maps to SOLID + Separation of Concerns.