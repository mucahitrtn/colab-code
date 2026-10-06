# Where this can go

The current release is a tested single-model recipe and a small terminal wrapper.

- [ ] Add a single lifecycle command for allocation, readiness checks, and tunnel management.
- [ ] Validate additional GPU configurations with memory and billing observations.
- [ ] Add a provider adapter for explicit Qwen thinking controls in Cline.
- [ ] Record native VS Code panel integration tests.
- [ ] Add several reproducible coding tasks with preserved baselines and unchanged tests.
- [ ] Parameterize model, session, and ports across local and remote scripts.

The scripts currently use the documented model, session name `qwen38-bf16`, and port 8000. `config/runtime.json` records settings; it is not a runtime configuration loader. Please open an issue before a large refactor.
