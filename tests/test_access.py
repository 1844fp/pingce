import hashlib
import json
from fastapi.testclient import TestClient
from apps.api.main import app


def test_token_project_and_write_scopes(monkeypatch):
    config=[{'sha256':hashlib.sha256(token.encode()).hexdigest(),'projects':['allowed'],'access':access} for token,access in [('read-token','read'),('write-token','write')]]
    monkeypatch.setenv('EVAL_AUTH_CONFIG',json.dumps(config))
    client=TestClient(app)
    assert client.get('/api/v1/runs').status_code==401
    headers={'Authorization':'Bearer read-token','X-Project':'allowed'}
    assert client.get('/api/v1/runs',headers=headers).status_code==200
    assert client.get('/api/v1/runs',headers=headers|{'X-Project':'other'}).status_code==403
    payload={'name':'scope','snapshot':'synthetic','cases':[{'id':'one','input':1,'expected':1}]}
    assert client.post('/api/v1/datasets',headers=headers,json=payload).status_code==403
    assert client.post('/api/v1/datasets',headers=headers|{'Authorization':'Bearer write-token'},json=payload).status_code==201
    assert client.get('/api/v1/health').status_code==200


def test_invalid_config_fails_closed(monkeypatch):
    client=TestClient(app)
    for value in ['invalid','[]','[{"sha256":"bad"}]']:
        monkeypatch.setenv('EVAL_AUTH_CONFIG',value)
        assert client.get('/api/v1/runs').status_code==503
