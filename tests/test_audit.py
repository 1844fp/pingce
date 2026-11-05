import uuid
from fastapi.testclient import TestClient
from apps.api.main import app,connection


def test_audit_chain_scope_and_change_detection():
    client=TestClient(app);project='audit-'+uuid.uuid4().hex
    headers={'X-Project':project}
    response=client.post('/api/v1/datasets',headers=headers,json={'name':'synthetic','snapshot':'fixed','cases':[{'id':'a','input':1,'expected':1}]})
    assert response.status_code==201
    audit=client.get('/api/v1/audit',headers=headers).json()
    assert audit['chain_valid'] and audit['total']==1
    assert audit['events'][0]['action']=='dataset.created'
    assert client.get('/api/v1/audit',headers={'X-Project':project+'-other'}).json()['total']==0
    with connection() as db:
        db.execute("UPDATE audit_events SET action='tampered' WHERE project=?",(project,))
    assert client.get('/api/v1/audit',headers=headers).json()['chain_valid'] is False
