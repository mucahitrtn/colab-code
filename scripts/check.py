"""CPU-only release checks; never connects to Colab or imports GPU packages."""
from pathlib import Path
import ast
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
files = [root / 'qwen']
for folder in ('client', 'colab', 'scripts', 'tests', 'benchmarks/agent_fixture'):
    files.extend((root / folder).glob('*.py'))
for path in files:
    ast.parse(path.read_text(), filename=str(path))
subprocess.run([sys.executable, str(root / 'qwen'), '--help'], check=True, stdout=subprocess.DEVNULL)
result = subprocess.run([sys.executable, str(root / 'qwen'), '--timeout', '-1', 'test'], capture_output=True, text=True)
assert result.returncode == 2 and '--timeout must be 0 or greater' in result.stderr, result.stderr
result = subprocess.run([sys.executable, str(root / 'qwen'), '--cwd', str(root / '.nonexistent-check-dir'), 'test'], capture_output=True, text=True)
assert result.returncode == 2 and 'Project directory does not exist' in result.stderr, result.stderr
subprocess.run([sys.executable, '-m', 'unittest', '-v'], cwd=root / 'benchmarks/agent_fixture', check=True)
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=root, check=True)
print(f'Syntax checked: {len(files)} files; CLI validation, fixture tests and model-budget tests passed.')
