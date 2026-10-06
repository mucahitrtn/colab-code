"""Read setup/server progress without printing credentials."""
from pathlib import Path
import json
import subprocess

root = Path('/content/qwen38-bf16')
for name in ('setup-status.json', 'model-revision.json'):
    path = root / name
    if path.exists():
        print(name, path.read_text())
for name in ('setup.log', 'server.log'):
    path = root / name
    if path.exists():
        print(f'Last lines: {name}')
        lines = path.read_text(errors='replace').splitlines()[-12:]
        # Keys are kept in environment/files, never passed on the command line.
        print('\n'.join(lines))
subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv'])
