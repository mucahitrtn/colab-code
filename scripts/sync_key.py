"""Fetch the runtime API key through SSH without printing it to the terminal."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
runtime = root / '.runtime'
source = runtime / 'get_key.py'
source.write_text('from pathlib import Path\nprint(Path("/content/qwen38-bf16/api-key").read_text().strip())\n')
result = subprocess.run([sys.executable, str(root / 'client/remote.py'), str(source)],
                        stdout=subprocess.PIPE, check=True)
key = result.stdout.decode().strip()
if not key or any(c.isspace() for c in key) or len(key) < 32:
    raise SystemExit('SSH did not return a valid key; existing local key was preserved.')
path = runtime / 'api-key'
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.fchmod(fd, 0o600)
with os.fdopen(fd, 'w') as handle:
    handle.write(key)
print('API key saved privately to .runtime/api-key.')
