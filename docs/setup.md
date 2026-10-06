# From Colab credits to a local coding agent

## 1. Install local tools

In the cloned repository, run `./qwen setup`. It installs Google Colab CLI 0.7.4 in `.venv`, Cline CLI 3.0.68 in `.runtime`, and creates a dedicated SSH key. Google credentials remain in the Colab CLI's own local configuration. Runtime keys and agent state are git-ignored.

Run the CLI and complete its authentication flow when prompted:

```bash
.venv/bin/colab sessions
.venv/bin/colab usage
```

The [official Colab CLI documentation](https://github.com/googlecolab/google-colab-cli) covers authentication and account access. If your CLI requests an explicit login step, use its `--help` instructions.

## 2. Allocate and inspect the GPU

This recipe was tested with Colab's G4 allocation, providing an NVIDIA RTX PRO 6000 Blackwell Server Edition with 97,887 MiB VRAM. The GPU label alone does not establish capacity; inspect your actual allocation. Availability depends on your account and Colab.

```bash
.venv/bin/colab new -s qwen38-bf16 --gpu G4
.venv/bin/colab exec -s qwen38-bf16 -f colab/inspect_runtime.py --timeout 60
```

Before continuing, check BF16 support, VRAM, RAM, and disk space. The tested runtime started with ~192 GiB free disk; the model checkpoint alone is ~55.6 GB, and installation needs additional space. This configuration has not been validated on an 80 GB A100/H100.

## 3. Download the pinned model and start vLLM

```bash
.venv/bin/colab exec -s qwen38-bf16 -f colab/bootstrap.py --timeout 60
.venv/bin/colab exec -s qwen38-bf16 -f colab/progress.py --timeout 30
```

Bootstrap runs in the background. Repeat the progress command until `stage` is `ready`; on `failed`, inspect the reported error before restarting. It installs an isolated `uv` environment with vLLM 0.31.0, Transformers `>=5.10.4,<5.18.0`, and ninja. The pinned model revision is `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.

```bash
.venv/bin/colab exec -s qwen38-bf16 -f colab/start_server.py --timeout 30
.venv/bin/colab exec -s qwen38-bf16 -f colab/progress.py --timeout 30
```

Server startup is also asynchronous. Wait for the log to show that the API is ready. Settings: BF16, 131,072 context, one concurrent sequence, 85% GPU memory target, text-only, Qwen reasoning and tool parsers. The server binds to `127.0.0.1:8000` and creates its API key privately.

## 4. Open the tunnel

Keep this running in terminal A:

```bash
./qwen tunnel
```

In terminal B, in the repository:

```bash
./qwen sync-key
./qwen smoke
```

The tunnel uses Colab's WebSocket SSH bridge and a shared SSH control socket. The CLI supports one independent SSH connection to this runtime; use multiplexed commands while the tunnel is open:

```bash
python3 client/remote.py colab/progress.py
```

Avoid notebook-kernel execution while SSH is active. To restart the server through this connection, use `python3 client/remote.py colab/start_server.py` after resolving the original error. The server refuses to launch a duplicate live process.

## 5. Ask it to code

```bash
./qwen --cwd /path/to/your/project
./qwen --cwd /path/to/your/project --timeout 0 \
  'Find the failing test, explain the cause, fix it, and run the relevant tests.'
```

The working directory controls which project the local agent operates in. Tool actions are auto-approved by default; `--auto-approve false` requests approvals. Ctrl-C exits the agent or tunnel; it does not terminate the Colab runtime.

## VS Code panel (optional)

Install Cline and choose **OpenAI Compatible**:

| Setting | Value |
| --- | --- |
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `Qwen/Qwen3.8-27B` |
| API key | Value stored privately in `.runtime/api-key` |
| Input context budget | `122880` for the 131,072-token server |
| Maximum output | `8192` |
| Image support | Disabled for this server |

The panel configuration is separate from the isolated CLI state. The terminal CLI was tested; panel operation is not part of the recorded pilot. See [Cline's provider guide](https://docs.cline.bot/provider-config/openai-compatible).

## Stop compute consumption

```bash
.venv/bin/colab stop -s qwen38-bf16
.venv/bin/colab usage
```

Colab runtimes are ephemeral. `/content` files can disappear after termination. The server installation records its revision and package list under `/content/qwen38-bf16`; the repository also includes the pilot's metadata in `config/`.

## Troubleshooting

- **Connection refused:** inspect server progress/logs and ensure terminal A still has the tunnel open.
- **Missing local key/provider:** complete `./qwen setup`, then `./qwen sync-key` after starting the server.
- **Host key changed after replacing the runtime:** verify that the session is the new runtime, then remove the old alias with `ssh-keygen -R qwen38-bf16 -f .runtime/known_hosts` and reopen the tunnel.
- **GPU out of memory:** this recipe is validated only on the documented 96 GB GPU. Context/KV cache consume memory beyond the ~50.22 GiB weights; choose new settings deliberately and record them.
- **Windows:** use WSL and validate Colab CLI connectivity there; native Windows has not been tested.

## Context limits

The original pilot deliberately capped vLLM at 32,768 tokens. The pinned model configuration has `max_position_embeddings: 262144`; this is a model capability, not a guarantee of GPU capacity or coding quality at that length. The launcher now defaults to 131,072. The original hardware log reported a 414,378-token KV pool at 32K; a new startup and live test are still required to validate a larger setting.

The terminal wrapper reads `max_model_len` from `/v1/models` on every launch and sets Cline's input budget to that limit minus 8,192 output tokens. This avoids the generic provider's 128,000-token default being larger than a 32K server. Restart the local agent to apply changed settings. Existing conversations can still exceed any finite context window; large file/tool results and token estimation can also require a new conversation.

`colab/start_server.py --max-model-len N` accepts 16,384 through 262,144 tokens when executed as a file. When using `colab exec -f` or the stdin SSH helper, edit the launcher's default before sending it. Changing a running server's limit requires stopping and restarting its vLLM process; editing a file alone does not change the live API.

### Change context from your terminal

With the SSH tunnel open:

```bash
./qwen context           # read current server/input/output budgets
./qwen context 65536     # select 64K
./qwen context 131072    # select 128K
./qwen context 48000     # custom limits work too
```

Stop all agent clients first. The command checks the model's native limit on the runtime, refuses to stop a server with active or queued requests, verifies the server PID, archives its log, and restarts it using the selected value. It waits up to 180 seconds for the API to advertise the new limit. The idle check is a snapshot, not a lock: keep clients stopped until the command finishes.

If the server is already using the requested value, the command does not restart it. If a previous startup failed and its process has exited, you can retry a smaller value. If a live process is unresponsive, the command refuses to stop it without determining its request state; inspect runtime logs. This tool configures the current runtime, not future fresh allocations, which use the launcher's default.

Then launch `./qwen` again so the agent reads the new budgets. The 8,192-token output reservation is maintained. Larger contexts still need model-backed validation; the current recorded long-context pilot reaches 32K only.
