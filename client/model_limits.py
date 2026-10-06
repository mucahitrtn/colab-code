"""Align the agent's prompt/output budgets with the live vLLM server."""
import json
import urllib.request


def model_budgets(models, model_id):
    model = next((item for item in models['data'] if item['id'] == model_id), None)
    if model is None:
        raise ValueError(f'Server does not advertise {model_id}.')
    length = model.get('max_model_len')
    if isinstance(length, bool) or not isinstance(length, int) or length < 16384:
        raise ValueError('Server must advertise max_model_len >= 16384 in /v1/models.')
    output = 8192
    return {'contextWindow': length - output, 'maxTokens': output}


def fetch_model_budgets(base_url, api_key, model_id):
    request = urllib.request.Request(base_url.rstrip('/') + '/models',
                                     headers={'Authorization': f'Bearer {api_key}'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return model_budgets(json.load(response), model_id)
