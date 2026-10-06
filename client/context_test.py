"""Probe approximately 8K, 16K and 32K total context; record actual token usage."""
from pathlib import Path
import json
import time
import urllib.request

root = Path(__file__).resolve().parents[1]
key = (root / '.runtime/api-key').read_text().strip()
results = []
for repeats in (8000, 16000, 32000):
    marker = 'CTX_PILOT_7429'
    content = f'Remember this passcode: {marker}.\n'
    content += ' sample' * repeats
    content += '\nReturn only the passcode given at the beginning.'
    payload = {'model': 'Qwen/Qwen3.8-27B', 'messages':[{'role':'user','content':content}],
               'max_tokens':64, 'temperature':0.7,
               'chat_template_kwargs':{'enable_thinking':False}}
    start = time.perf_counter()
    req = urllib.request.Request('http://127.0.0.1:8000/v1/chat/completions',
        data=json.dumps(payload).encode(), headers={'Content-Type':'application/json',
        'Authorization':f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=180) as response:
        answer = json.load(response)
    text = answer['choices'][0]['message'].get('content') or ''
    result = dict(repeats=repeats, seconds=round(time.perf_counter()-start,3),
                  usage=answer.get('usage'), content=text, retrieved=marker in text)
    results.append(result)
    (root/'benchmarks/context-results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(result), flush=True)
    assert result['retrieved'], result
