# Evidence, not a leaderboard

The recorded pilot used Qwen/Qwen3.8-27B BF16 on a 96 GB RTX PRO 6000 Blackwell GPU, vLLM 0.31.0, and local Cline CLI 3.0.68. [Runtime settings](../config/runtime.json), [model revision](../config/model-revision.json), and [remote packages](../config/remote-packages.txt) record the environment. The bootstrap now pins that revision and explicitly installs ninja, which was needed by the tested server.

## API integration

[smoke-results.json](../benchmarks/smoke-results.json) records model identity, unauthenticated rejection (401), generated output, streaming completion, separate reasoning output, and a two-turn tool exchange. The tool test returns a mocked file result to the model; the local-agent pilot below exercises actual file and terminal tools. Re-run with `./qwen smoke` against your live server; it overwrites the smoke report.

## Local agent task

[agent-results.json](../benchmarks/agent-results.json) records one Python function repair. The agent had to trim tags, omit empty strings, deduplicate while retaining first-seen order, and preserve case. Before the repair, 2 tests passed and 3 failed. Cline read files, edited the implementation, and executed local tests. Independent verification passed all 5 tests; the test file was not changed.

The fixture in this repository contains the **fixed implementation**. Running its tests verifies the final artifact; it does not repeat the original repair task. [Task description](../benchmarks/tasks.md).

```bash
cd benchmarks/agent_fixture
python3 -m unittest -v
```

## Synthetic context recall

[context-results.json](../benchmarks/context-results.json) records a marker-retrieval test with repeated filler at 8,039, 16,039, and 32,039 prompt tokens. All three returned the marker without an observed OOM. Run `python3 client/context_test.py` against a live server to repeat it; the script overwrites the report.

This does not establish long-repository reasoning, coding accuracy, sustained throughput, or a model ranking. The recorded timings have tiny output lengths and should not be advertised as general generation speed. No Claude Code comparison was performed.

## CI scope

GitHub Actions checks Python syntax, CLI help/argument handling, and the fixed fixture tests. It does not allocate a Colab GPU or run model inference. Contributions claiming support for another GPU should include their exact settings and actual integration results.
