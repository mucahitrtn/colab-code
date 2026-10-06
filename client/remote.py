"""Execute one Python file through the authenticated Colab SSH connection."""
from pathlib import Path
import shlex
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
key = root / '.runtime/colab_ed25519'
proxy = shlex.join([str(root / '.venv/bin/colab'), 'ssh', '--proxy-mode',
                    '-s', 'qwen38-bf16', '-i', str(key)])
args = ['ssh', '-S', str(root / '.runtime/ssh-control'), '-o', f'ProxyCommand={proxy}',
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', f'UserKnownHostsFile={root / ".runtime/known_hosts"}',
        '-o', 'HostKeyAlias=qwen38-bf16', '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=30', '-i', str(key), 'root@colab-runtime', 'python3 -']
with Path(sys.argv[1]).open('rb') as source:
    raise SystemExit(subprocess.call(args, stdin=source))
