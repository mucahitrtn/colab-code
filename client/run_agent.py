"""Run isolated Cline CLI against the Colab model."""
from pathlib import Path
import argparse
import json
import os
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--cwd', type=Path, default=Path.cwd())
parser.add_argument('--prompt')
parser.add_argument('--interactive', action='store_true', help='Open the terminal chat interface.')
parser.add_argument('--timeout', type=int, help='Seconds; 0 disables the task timeout.')
parser.add_argument('--auto-approve', choices=['true', 'false'], default='true')
args = parser.parse_args()
if not args.cwd.is_dir():
    parser.error(f'Project directory does not exist: {args.cwd}')
if args.timeout is not None and args.timeout < 0:
    parser.error('--timeout must be 0 or greater.')
if not args.prompt and not args.interactive:
    parser.error('Provide --prompt, or use --interactive for terminal chat.')
state = root / '.runtime/cline-state'
path = state / 'settings/providers.json'
if not path.exists():
    raise SystemExit('Configure the isolated CLI provider first; see README.md.')
data = json.loads(path.read_text())
data['providers']['openai-compatible']['settings']['apiKey'] = (root / '.runtime/api-key').read_text().strip()
path.write_text(json.dumps(data, indent=2))
path.chmod(0o600)
env = os.environ.copy()
env['CLINE_LOG_ENABLED'] = '0'
command = [str(root / '.runtime/cline-cli/node_modules/cline/bin/cline'),
           '--data-dir', str(state), '--provider', 'openai-compatible',
           '--model', 'Qwen/Qwen3.8-27B', '--thinking', 'none',
           '--compaction', 'basic', '--auto-approve', args.auto_approve, '--cwd', str(args.cwd.resolve())]
timeout = args.timeout if args.timeout is not None else (0 if args.interactive else 180)
if timeout:
    command.extend(['--timeout', str(timeout)])
if args.interactive:
    command.append('--tui')
if args.prompt:
    command.append(args.prompt)
raise SystemExit(subprocess.call(command, env=env))
