"""Start the authenticated model API on the runtime's loopback interface."""
from pathlib import Path
import json
import os
import secrets
import subprocess

root = Path('/content/qwen38-bf16')
status = json.loads((root / 'setup-status.json').read_text())
if status['stage'] != 'ready':
    raise RuntimeError(f"Setup is not ready: {status['stage']}")
pid_file = root / 'server.pid'
if pid_file.exists():
    pid = int(pid_file.read_text())
    try:
        os.kill(pid, 0)
        if Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0] != 'Z':
            raise RuntimeError('Server already running.')
    except ProcessLookupError:
        pass
key_file = root / 'api-key'
if not key_file.exists():
    key_file.write_text(secrets.token_urlsafe(32))
key_file.chmod(0o600)
env = os.environ.copy()
env['PATH'] = str(root / 'venv/bin') + os.pathsep + env.get('PATH', '')
env['VLLM_API_KEY'] = key_file.read_text().strip()
env['VLLM_NO_USAGE_STATS'] = '1'
env['NO_COLOR'] = '1'
args = [
    str(root / 'venv/bin/vllm'), 'serve', str(root / 'model'),
    '--served-model-name', 'Qwen/Qwen3.8-27B',
    '--host', '127.0.0.1', '--port', '8000',
    '--dtype', 'bfloat16', '--max-model-len', '32768',
    '--max-num-seqs', '1', '--gpu-memory-utilization', '0.85',
    '--language-model-only', '--reasoning-parser', 'qwen3',
    '--enable-auto-tool-choice', '--tool-call-parser', 'qwen3_xml',
]
with (root / 'server.log').open('w') as log:
    process = subprocess.Popen(args, env=env, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
pid_file.write_text(str(process.pid))
(root / 'server-command.json').write_text(json.dumps(args, indent=2))
print(json.dumps({'server_pid': process.pid, 'host': '127.0.0.1', 'port': 8000}))
