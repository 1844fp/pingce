import hashlib
import uuid
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api import artifacts


def test_report_archive_and_scope(tmp_path,monkeypatch):
    store=artifacts.ArtifactStore(tmp_path/'store')
    monkeypatch.setattr(artifacts,'put',store.put)
    monkeypatch.setattr(artifacts,'get',store.get)
    client=TestClient(app);project='archive-'+uuid.uuid4().hex;headers={'X-Project':project}
    ds=client.post('/api/v1/datasets',headers=headers,json={'name':'synthetic','snapshot':'fixed','cases':[{'id':'x','input':1,'expected':1}]}).json()
    tg=client.post('/api/v1/targets',headers=headers,json={'name':'synthetic','adapter':'fixture','revision':'1'}).json()
    run=client.post('/api/v1/runs',headers=headers|{'Idempotency-Key':str(uuid.uuid4())},json={'name':'archive','dataset_id':ds['id'],'target_id':tg['id']}).json()
    archived=client.post(f"/api/v1/runs/{run['id']}/archive",headers=headers)
    assert archived.status_code==201,archived.text
    meta=archived.json();download=client.get('/api/v1/artifacts/'+meta['id'],headers=headers)
    assert download.status_code==200 and 'attachment' in download.headers['content-disposition']
    assert hashlib.sha256(download.content).hexdigest()==meta['sha256']
    assert download.json()['run']['id']==run['id']
    assert client.get('/api/v1/artifacts/'+meta['id'],headers={'X-Project':project+'other'}).status_code==404
    assert client.get('/api/v1/audit',headers=headers).json()['events'][-1]['action']=='report.archived'
    client.post(f"/api/v1/runs/{run['id']}/cancel",headers=headers)
