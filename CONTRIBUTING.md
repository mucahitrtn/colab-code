# Contributing

Small, reproducible improvements are welcome: a clearer setup step, a bug fix, a verified GPU configuration, or a coding task with a preserved baseline.

1. Open an issue for significant changes.
2. Include the environment, command, expected behavior, and observed result.
3. Keep credentials, account balances, SSH keys, private project code, and agent state out of commits.
4. Run `python3 scripts/check.py` before submitting a pull request.

Model-backed claims need actual GPU results and a description of limitations. CPU CI cannot prove inference support. This repository does not redistribute model weights.
