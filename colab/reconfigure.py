"""Idle-only server reconfiguration; embedded by the local context command."""
from pathlib import Path
import json
import os
import signal
import sys
import time
import urllib.request


def validate_length(length, native_limit):
    if isinstance(length, bool) or not isinstance(length, int) or not 16384 <= length <= native_limit:
        raise ValueError(f'Context must be an integer between 16384 and {native_limit}.')


def has_active_requests(metrics):
    counters = [line for line in metrics.splitlines()
                if line.startswith(('vllm:num_requests_running{', 'vllm:num_requests_waiting{'))]
    if not counters:
        raise ValueError('Request counters missing; refusing to interrupt an unknown server state.')
    return any(float(line.rsplit(' ', 1)[1]) > 0 for line in counters)


def restart(length, server_source):
    root = Path('/content/qwen38-bf16')
    native = json.loads((root / 'model/config.json').read_text())['text_config']['max_position_embeddings']
    validate_length(length, native)
    pid_file = root / 'server.pid'
    pid = int(pid_file.read_text()) if pid_file.exists() else None
    alive = False
    if pid is not None:
        try:
            os.kill(pid, 0)
            alive = Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0] != 'Z'
        except (ProcessLookupError, FileNotFoundError):
            pass
    if alive:
        command = Path(f'/proc/{pid}/cmdline').read_bytes()
        if b'vllm' not in command or b'/content/qwen38-bf16/model' not in command or os.getpgid(pid) != pid:
            raise RuntimeError('Server PID identity mismatch; nothing was stopped.')
        headers = {'Authorization': 'Bearer ' + (root / 'api-key').read_text().strip()}
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/v1/models', headers=headers), timeout=10) as response:
            models = json.load(response)['data']
        if any(m['id'] == 'Qwen/Qwen3.8-27B' and m.get('max_model_len') == length for m in models):
            print(json.dumps({'context': length, 'changed': False}))
            return
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/metrics', headers=headers), timeout=10) as response:
            if has_active_requests(response.read().decode()):
                raise RuntimeError('Active or queued requests: stop the local agent, then retry. Nothing was stopped.')
        # The idle check is a snapshot. Stop agent clients before reconfiguration
        # so another request cannot arrive between this check and SIGTERM.
        os.killpg(pid, signal.SIGTERM)
        for _ in range(60):
            try:
                if Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0] == 'Z':
                    break
            except FileNotFoundError:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('Old server did not exit; inspect it before retrying.')
    log = root / 'server.log'
    if log.exists():
        log.replace(root / f'server-before-context-{time.time_ns()}.log')
    sys.argv = ['start_server.py', '--max-model-len', str(length)]
    exec(compile(server_source, 'start_server.py', 'exec'), {'__name__': '__main__'})
