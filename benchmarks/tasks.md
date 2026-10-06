# Local-agent pilot task

Working directory: `benchmarks/agent_fixture/`.

Repair `normalize_tags` in `tags.py`. Input is a list of strings. Trim surrounding whitespace, skip empty tags, remove duplicates while preserving first-seen order, and preserve case distinctions. Do not modify the test file. Run `python3 -m unittest -v` and fix the implementation until all tests pass.

Acceptance: actual file reads and edits, unchanged tests, five passing tests, and independent verification. This is a connection/agent pilot, not a comprehensive coding benchmark. The checked-in implementation is the final repaired version.
