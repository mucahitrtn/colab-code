"""Install local tools without creating or charging a Colab runtime."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
for executable in ('npm', 'node', 'ssh', 'ssh-keygen'):
    if not shutil.which(executable):
        raise SystemExit(f'Missing {executable}; install Node.js 22+ and OpenSSH first.')
node_major = int(subprocess.check_output(['node', '--version'], text=True).strip().lstrip('v').split('.')[0])
if node_major < 22:
    raise SystemExit('Node.js 22 or newer is required.')
runtime = root / '.runtime'
runtime.mkdir(mode=0o700, exist_ok=True)
subprocess.run([sys.executable, '-m', 'venv', str(root / '.venv')], check=True)
subprocess.run([str(root / '.venv/bin/python'), '-m', 'pip', 'install', '-r', str(root / 'requirements-local.txt')], check=True)
subprocess.run(['npm', 'install', '--prefix', str(runtime / 'cline-cli'), 'cline@3.0.68'], check=True)
key = runtime / 'colab_ed25519'
if not key.exists():
    subprocess.run(['ssh-keygen', '-t', 'ed25519', '-N', '', '-f', str(key), '-C', 'colab-code'], check=True)
provider = runtime / 'cline-state/settings/providers.json'
if not provider.exists():
    subprocess.run([str(runtime / 'cline-cli/node_modules/cline/bin/cline'), 'auth',
                    '--provider', 'openai-compatible', '--apikey', 'placeholder',
                    '--modelid', 'Qwen/Qwen3.8-27B', '--baseurl', 'http://127.0.0.1:8000/v1',
                    '--data-dir', str(runtime / 'cline-state')], check=True)
print('Local tools ready. Next: follow docs/setup.md to create the GPU runtime.')
