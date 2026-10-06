# Launch copy

## Short post

Your laptop can't fit a 27B model. Your Colab GPU can.

Colab Code connects Qwen3.8-27B BF16 on a 96 GB Colab GPU to a Cline coding agent in your local terminal. Keep VS Code. Let the agent edit your files and run your tests.

Open source. Pinned setup. Real pilot evidence. No public inference URL required.

Try it, share your GPU results, and star it if it helps:
https://github.com/mucahitrtn/colab-code

## Longer introduction

Have spare Colab compute credits and want to use them for coding? Colab Code is a practical recipe for cloud GPU inference with local agent tools. Qwen runs through vLLM in Colab; Cline reads, edits, and tests your project on your laptop through an authenticated SSH tunnel.

We tested a full BF16 27B checkpoint on a 96 GB Blackwell GPU, an API tool exchange, one real local function repair, and synthetic context recall up to 32K input tokens. These are integration checks, not a coding leaderboard.

The repository includes setup scripts, an interactive terminal entry point, raw pilot reports, and a roadmap. Contributions with reproducible results on other GPUs are welcome.
