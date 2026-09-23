# LLM Council Architecture Specification & Invariant

Whenever executing complex tasks, audits, design phases, or implementations, adhere to the **LLM Council Approach**:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                           LLM Council                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │    CLI      │───▶│  Council    │───▶│     Orchestrator        │ │
│  │  (typer)    │    │   (API)     │    │                         │ │
│  └─────────────┘    └─────────────┘    │  ┌───────────────────┐  │ │
│                                        │  │  Health Checker   │  │ │
│  ┌─────────────────────────────────┐   │  ├───────────────────┤  │ │
│  │        Provider Registry        │◀──│  │ Degradation Policy│  │ │
│  │  ┌─────────┐ ┌─────────┐       │   │  ├───────────────────┤  │ │
│  │  │OpenRouter│ │Anthropic│ ...  │   │  │  Artifact Store   │  │ │
│  │  └─────────┘ └─────────┘       │   │  └───────────────────┘  │ │
│  └─────────────────────────────────┘   └─────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Subagent Configs                          │   │
│  │  router | planner | researcher | drafter | critic | ...     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     JSON Schemas                             │   │
│  │  Validation & retry logic for structured outputs             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Council Roles & Responsibilities

1. **Router Subagent**:
   - Classifies task domain (physics, math, neural dynamics, architecture, validation).
   - Identifies required dependencies, toolchains, and constraints.

2. **Planner Subagent**:
   - Outlines sequential stages with explicit falsification conditions.
   - Forbids premature victory declarations without prior verification gates.

3. **Researcher Subagent**:
   - Reads executable code, configurations, and raw telemetry first before consulting reports or documentation.
   - Traces data paths end-to-end to identify hidden assumptions or privileged leaks.

4. **Drafter Subagent**:
   - Implements minimal, clean, type-annotated code and structured JSON schemas.
   - Enforces validation and retry logic on all structured outputs.

5. **Critic / Adversarial Auditor Subagent**:
   - Rigorously stress-tests every claim against ground truth.
   - Identifies circular reasoning, inflated baselines, and harness-level shortcuts.
   - Forbids promotional language, euphemisms, and false equivalence.

6. **Orchestrator & Health Checker**:
   - Validates outputs against strict JSON schemas.
   - Manages graceful degradation and failure recovery.
   - Persists intermediate and final deliverables to the artifact store.
