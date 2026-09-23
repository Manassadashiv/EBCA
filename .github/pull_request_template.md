## Description
Briefly describe the purpose of this PR and which developmental stage/mechanism it impacts.

## Architectural Invariant Checklist
- [ ] **Roadmap Alignment**: Declares alignment with current developmental milestone.
- [ ] **AST Anti-Cheat Scan**: Confirmed zero simulator coordinates (`qpos`, `qvel`, `geom_xpos`, `mj_ray`) in the cognitive decision pipeline.
- [ ] **Timestep Derived from Config**: Uses exact simulation timestep `model.opt.timestep * substeps`.
- [ ] **Unification Over Fragmentation**: Integrates with the canonical organism on the zero-copy bus.
- [ ] **Deterministic Verification**: Tested against pre-registered seeds.
