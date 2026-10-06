"""Inspect or change the live server context from the local terminal."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from colab.reconfigure import validate_length
from client.model_limits import model_budgets


def models():
    key = (root / '.runtime/api-key').read_text().strip()
    req = urllib.request.Request('http://127.0.0.1:8000/v1/models', headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description='Show live context, or restart the idle Colab server with a chosen token limit.')
    parser.add_argument('tokens', type=int, nargs='?', help='16384–262144 tokens; omit to inspect. Stop agent clients before changing.')
    args = parser.parse_args()
    if args.tokens is not None:
        try:
            validate_length(args.tokens, 262144)
        except ValueError as exc:
            parser.error(str(exc))
        source = (root / 'colab/reconfigure.py').read_text()
        starter = (root / 'colab/start_server.py').read_text()
        payload = source + '\nrestart(' + repr(args.tokens) + ', ' + repr(starter) + ')\n'
        with tempfile.TemporaryDirectory(prefix='colab-code-context-') as directory:
            script = Path(directory) / 'reconfigure.py'
            script.write_text(payload)
            print(f'Requesting {args.tokens:,} tokens. Active requests prevent a restart.', flush=True)
            result = subprocess.run([sys.executable, str(root / 'client/remote.py'), str(script)])
            if result.returncode:
                return result.returncode
        print('Waiting for the server (up to 180 seconds)...', flush=True)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            try:
                data = models()
                if any(m['id'] == 'Qwen/Qwen3.8-27B' and m.get('max_model_len') == args.tokens for m in data['data']):
                    break
            except (OSError, ValueError):
                pass
            time.sleep(2)
        else:
            raise SystemExit('Server not ready. Inspect: python3 client/remote.py colab/progress.py. If startup failed, retry a smaller context.')
    else:
        data = models()
    budget = model_budgets(data, 'Qwen/Qwen3.8-27B')
    print(json.dumps({'server_context_tokens': budget['contextWindow'] + budget['maxTokens'],
                      'agent_input_budget': budget['contextWindow'],
                      'agent_output_budget': budget['maxTokens']}, indent=2))
    if args.tokens is not None:
        print('Context is live. Start a new ./qwen process to load the updated agent budgets.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        raise SystemExit(f'Cannot read the context: {exc}. Check the server and tunnel.') from exc
