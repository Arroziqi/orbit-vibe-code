# TEST — Constitution Validation Protocol

**Status:** Companion to CONSTITUTION.md
**Purpose:** Provide a repeatable, mechanical way to validate ANY generated code against the constitution before acceptance.
**Scope:** Language-agnostic checklists, code-search probes, and dynamic test templates.

---

## 1. How to Use This Protocol

1. Run the **Static Probes** (Section 2) — quick source scans to catch prohibited practices.
2. Apply the **Rule Mapping Rubric** (Section 3) — line-by-line constitution compliance.
3. Run the **Mandatory Dynamic Tests** (Section 4) — behavior verification.
4. Produce a **Validation Verdict** (Section 5).
5. Anything failing a `MUST`/`NEVER` rule → reject and fix before acceptance.

---

## 2. Static Probes (code-search based)

These probes MUST be executed against the submitted code. A hit is a finding to resolve (some hits are legal; each MUST be triaged).

| # | Probe (search pattern) | Finding | Verdict if confirmed |
| --- | --- | --- | --- |
| P1 | Module-level mutable collections holding state (e.g. top-level `users = {}` / `tasks = []` populated at runtime) | Global state | VIOLATION of 7.1 / NEVER-1 |
| P2 | `print(` used for operational logging (outside CLI/tooling layer) | Wrong logging | VIOLATION of 8.1 / NEVER-5 |
| P3 | Bare catch / `except:` with no handling or re-raise | Silent swallow | VIOLATION of 8.5 / NEVER-6 |
| P4 | Direct system time call (`datetime.now()`, `time()` ) inside domain/use-case code | Hidden clock | VIOLATION of 3.6 / 9.2 / NEVER-4 |
| P5 | Dispatch on action name in executor/scheduler (`if action ==` / `switch(action)`) | OCP breach | VIOLATION of 6.2 / NEVER-2 |
| P6 | More than one check comparing `executed` against `quota` | Duplicated rule | VIOLATION of 4.3 / NEVER-3 |
| P7 | Two or more cyclic imports (a↔b) | Circular dependency | VIOLATION of 5.1 / NEVER-7 |
| P8 | Business rules written inside composition root / orchestration entry | Wrong layer | VIOLATION of 4.4 / NEVER-8 |
| P9 | Hard-coded user/task definitions inside domain or use-case modules | Config leakage | VIOLATION of 3.7 / NEVER-9 |
| P10 | Duplicated config validation or outcome-handling blocks | DRY breach | SHOULD fix (4.3) |

---

## 3. Rule Mapping Rubric

Score each rule as **PASS / FAIL / N/A**. Any `MUST`/`NEVER` = FAIL ⇒ reject submission.

| Const. § | Check | Method |
| --- | --- | --- |
| 3.1 | Per-day counter; rollover mechanism exists | Dynamic test T2 + code review |
| 3.2 | Multi-task per user at same time supported | Dynamic test T4 |
| 3.3 | Over-quota ⇒ skip + `quota_exceeded` log, not exception | Dynamic test T1 |
| 3.4 | Eligibility check defined once | Probe P6 |
| 3.5 | Check-and-increment atomic (no gap) | Code review + T1 stress |
| 3.6 | Clock injected, scheduler deterministic | Probe P4 + T3 |
| 3.7 | Config external + validated at boundary | Probe P9 + T5 |
| 4.1S | Each module single responsibility | Review: count reasons-to-change per module ≤ 1 |
| 4.1O | New action = new strategy + registration only | Probe P5 + T6 |
| 4.1L | Strategies honor contract (same outcomes/logging) | T6 stub inspection |
| 4.1I | Narrow role-based dependencies | Review import surface of each consumer |
| 4.1D | High-level depends on abstraction; wiring in root | Review constructor/imports; P8 |
| 4.2 | One-way deps, minimal public surface, acyclic | Import graph check; P7 |
| 4.3 | Each rule in exactly one place | Probes P6, P10 |
| 4.4 | domain/use case/infra/root separation | Review + P8 + import graph by layer |
| 5 | Layering respected; lower never knows higher | Import graph check |
| 6 | Action addition touches no executor/scheduler | Probe P5 + T6 |
| 7.1 | No global mutable state | Probe P1 |
| 7.2 | Explicit DI; no service-locator/global singleton | Review imports / globals |
| 7.3 | Invalid config rejected clearly at boundary | T5 |
| 7.4 | Clear naming; small functions | Review |
| 7.6 | Task/user records immutable after build | Review |
| 7.7 | Invalid state ⇒ clear typed error | Review exceptions |
| 8.1 | Logging facility used, not print | Probe P2 |
| 8.2 | Traceable log per execution path (user/task/action/outcome) | T7 assertion |
| 8.3 | Outcome taxonomy respected | T1/T4/T7 |
| 8.4 | One failing task cannot stop the loop | T8 |
| 8.5 | Small domain-meaningful exception set; no bare swallow | Probe P3 |
| 9.2 | Fake clock used in scheduler tests; no sleep/real time | Probe P4 in tests |
| 9.3 | Mandated cases covered | T1–T8 |

---

## 4. Mandatory Dynamic Tests

These MUST exist for the implementation and MUST pass. (Templates in language-agnostic terms; adapt idiomatically.)

| # | Test | Pass condition |
| --- | --- | --- |
| T1 | **Quota boundary set** — user with quota zero; quota `= executed`; quota one above executed | Eligible cases `executed`; boundary → `quota_exceeded`; count == quota after |
| T2 | **Daily rollover** — execute to quota on day 1, advance clock to day 2 | Executions succeed again; executed counter reset |
| T3 | **Determinism** — run scheduler twice with same injected time | Identical outcomes/logs; no wall-clock dependency |
| T4 | **Simultaneous tasks** — one user, 3 tasks at same time, quota 2 | First 2 `executed`, third `quota_exceeded` |
| T5 | **Config validation** — malformed task dict / unknown action | Clear validation error; system not corrupted |
| T6 | **Extensibility** — register stub strategy, schedule it | Runs via registry; executor/scheduler untouched |
| T7 | **Traceability** — run one task each outcome type | Every outcome produces complete log line (8.2 fields) |
| T8 | **Error isolation** — strategy raises; siblings same tick | Raising task logged `failed`; siblings still `executed` |

---

## 5. Validation Verdict

After Sections 2–4, emit one verdict:

```
STATUS         : APPROVED | REJECTED
VIOLATIONS     : <list of § / NEVER-ids>
SHOULD-DEVIATIONS : <list with justification>
PROBES TRIAGED : <P1..P10 results>
TESTS          : T1..T8 pass/fail
NEXT STEP      : <Proceed | Fix & re-run>
```

- **REJECTED** ⇒ any `MUST`/`NEVER` FAIL, any § — FAIL, or any mandated test failing.
- **APPROVED** ⇒ all checks pass; `SHOULD` deviations documented.