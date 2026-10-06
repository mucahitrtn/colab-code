"""Keep an SSH tunnel open: python client/tunnel.py. Ctrl-C closes only the tunnel."""
from pathlib import Path
import shlex
import subprocess

root = Path(__file__).resolve().parents[1]
key = root / '.runtime/colab_ed25519'
if not key.exists():
    raise SystemExit('Dedicated SSH key missing; see README.md.')
proxy = shlex.join([str(root / '.venv/bin/colab'), 'ssh', '--proxy-mode',
                    '-s', 'qwen38-bf16', '-i', str(key)])
args = ['ssh', '-N', '-L', '127.0.0.1:8000:127.0.0.1:8000',
        '-M', '-S', str(root / '.runtime/ssh-control'),
        '-o', f'ProxyCommand={proxy}', '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', f'UserKnownHostsFile={root / ".runtime/known_hosts"}',
        '-o', 'HostKeyAlias=qwen38-bf16', '-o', 'BatchMode=yes',
        '-i', str(key), 'root@colab-runtime']
print('Forwarding 127.0.0.1:8000 to Colab. Closing this tunnel does not stop GPU billing.', flush=True)
try:
    raise SystemExit(subprocess.call(args))
except KeyboardInterrupt:
    pass
