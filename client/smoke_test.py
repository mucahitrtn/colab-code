"""Check actual model output, streaming, auth and a complete tool round trip."""
from pathlib import Path
import json
import time
import urllib.request
import urllib.error

root = Path(__file__).resolve().parents[1]
key = (root / '.runtime/api-key').read_text().strip()
base = 'http://127.0.0.1:8000/v1'
model = 'Qwen/Qwen3.8-27B'


def request(path, payload=None, authenticated=True):
    headers = {'Content-Type': 'application/json'}
    if authenticated:
        headers['Authorization'] = f'Bearer {key}'
    return urllib.request.urlopen(urllib.request.Request(base + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers), timeout=180)


def completion(messages, **extra):
    payload = dict(model=model, messages=messages, max_tokens=1024,
                   temperature=0.7, chat_template_kwargs={'enable_thinking': False})
    payload.update(extra)
    with request('/chat/completions', payload) as response:
        return json.load(response)


results = {}
with request('/models') as response:
    ids = [item['id'] for item in json.load(response)['data']]
assert model in ids, ids
results['models'] = ids
try:
    request('/models', authenticated=False).close()
    raise AssertionError('Unauthenticated API access was accepted.')
except urllib.error.HTTPError as exc:
    assert exc.code == 401, exc.code
    results['auth'] = 'unauthenticated request rejected (401)'

start = time.perf_counter()
answer = completion([{'role': 'user', 'content': 'Yalnızca sonucu yaz: 17 * 19 kaçtır?'}])
content = answer['choices'][0]['message'].get('content') or ''
assert '323' in content, content
results['generation'] = dict(content=content, seconds=round(time.perf_counter()-start, 3), usage=answer.get('usage'))

answer = completion([{'role': 'user', 'content': 'What is 2 + 3? Give the final answer as a number.'}],
    chat_template_kwargs={'enable_thinking': True})
message = answer['choices'][0]['message']
reasoning = message.get('reasoning') or message.get('reasoning_content') or ''
assert reasoning and '5' in (message.get('content') or ''), message
assert '<think>' not in (message.get('content') or ''), message
results['reasoning_separation'] = dict(reasoning_chars=len(reasoning), content=message.get('content'))

payload = dict(model=model, messages=[{'role':'user','content':'Write exactly: STREAM_OK'}],
               max_tokens=128, stream=True, temperature=0.7,
               chat_template_kwargs={'enable_thinking': False})
pieces = []
done = False
with request('/chat/completions', payload) as response:
    for raw in response:
        line = raw.decode().strip()
        if line == 'data: [DONE]':
            done = True
        elif line.startswith('data: '):
            event = json.loads(line[6:])
            for choice in event.get('choices', []):
                pieces.append(choice.get('delta', {}).get('content') or '')
assert done and 'STREAM_OK' in ''.join(pieces), pieces
results['streaming'] = 'passed'

tools = [{'type':'function','function': {
    'name':'read_project_file', 'description':'Read a file from the project.',
    'parameters':{'type':'object','properties':{'path':{'type':'string'}},'required':['path']}}}]
messages = [{'role':'user','content':'Use read_project_file to read config.json. Report the project_name from that file. Do not guess it.'}]
answer = completion(messages, tools=tools, tool_choice='auto')
message = answer['choices'][0]['message']
calls = message.get('tool_calls') or []
assert len(calls) == 1, message
call = calls[0]
assert call['function']['name'] == 'read_project_file', call
arguments = json.loads(call['function']['arguments'])
assert arguments['path'].removeprefix('./') == 'config.json', arguments
messages.append({'role':'assistant','content':message.get('content'),'tool_calls':calls})
messages.append({'role':'tool','tool_call_id':call['id'],
                 'content':json.dumps({'project_name':'colab-bf16-pilot-7429'})})
answer = completion(messages, tools=tools)
content = answer['choices'][0]['message'].get('content') or ''
assert 'colab-bf16-pilot-7429' in content, answer
results['tool_round_trip'] = dict(arguments=arguments, content=content)
out = root / 'benchmarks'
out.mkdir(exist_ok=True)
(out / 'smoke-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(json.dumps(results, indent=2, ensure_ascii=False))
