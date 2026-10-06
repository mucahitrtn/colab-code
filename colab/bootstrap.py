"""Start isolated installation and pinned model download in the background."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path('/content/qwen38-bf16')
ROOT.mkdir(exist_ok=True)
WORKER = r'''
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys, traceback
ROOT = Path('/content/qwen38-bf16')
def status(stage, **fields):
    data = dict(stage=stage, time_utc=datetime.now(timezone.utc).isoformat(), **fields)
    temporary = ROOT / 'setup-status.tmp'
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(ROOT / 'setup-status.json')
    print(json.dumps(data), flush=True)
try:
    status('creating_venv')
    subprocess.run(['uv', 'venv', '--clear', '--python', sys.executable, str(ROOT / 'venv')], check=True)
    python = str(ROOT / 'venv/bin/python')
    status('installing')
    subprocess.run(['uv', 'pip', 'install', '--python', python, 'vllm==0.31.0', 'transformers>=5.10.4,<5.18.0', 'ninja'], check=True)
    status('downloading_model')
    subprocess.run([python, '-c', r"""
from huggingface_hub import HfApi, snapshot_download
from pathlib import Path
import json
root = Path('/content/qwen38-bf16')
info = HfApi().model_info('Qwen/Qwen3.8-27B', revision='1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0', files_metadata=True)
size = sum(f.size or 0 for f in info.siblings if f.rfilename.endswith('.safetensors'))
metadata = dict(model_id=info.id, revision=info.sha, safetensors_bytes=size)
(root / 'model-revision.json').write_text(json.dumps(metadata, indent=2))
print(json.dumps(metadata), flush=True)
snapshot_download('Qwen/Qwen3.8-27B', revision=info.sha, local_dir=str(root / 'model'),
    allow_patterns=['*.safetensors', '*.json', '*.jinja', '*.model', '*.txt'], max_workers=4)
"""], check=True)
    with (ROOT / 'packages.txt').open('w') as out:
        subprocess.run(['uv', 'pip', 'freeze', '--python', python], stdout=out, check=True)
    status('ready', revision=json.loads((ROOT / 'model-revision.json').read_text()))
except Exception as exc:
    traceback.print_exc()
    status('failed', error=str(exc))
    raise
'''
pid_file = ROOT / 'setup.pid'
if pid_file.exists():
    import os
    try:
        pid = int(pid_file.read_text())
        os.kill(pid, 0)
        state = Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0]
        if state != 'Z':
            raise RuntimeError('Setup already running; inspect setup-status.json before restarting.')
    except ProcessLookupError:
        pass
with (ROOT / 'setup.log').open('w') as log:
    process = subprocess.Popen([sys.executable, '-u', '-c', WORKER], stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
pid_file.write_text(str(process.pid))
print(json.dumps({'setup_pid': process.pid, 'directory': str(ROOT)}))
