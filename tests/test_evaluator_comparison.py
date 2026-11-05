import json
import uuid
from fastapi.testclient import TestClient
from apps.api.main import app,connection


def test_comparison_rejects_changed_evaluator_hash():
    client=TestClient(app)
    ds=client.post('/api/v1/datasets',json={'name':'哈希对比','snapshot':'synthetic','cases':[{'id':'one','input':1,'expected':1}]}).json()
    tg=client.post('/api/v1/targets',json={'name':'synthetic','adapter':'fixture','revision':'1'}).json()
    ids=[]
    for value in ['original','modified']:
        run=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'compare','dataset_id':ds['id'],'target_id':tg['id']}).json()
        ids.append(run['id'])
        with connection() as db:
            spec=run['spec'];spec['evaluator_hash']=value
            db.execute("UPDATE runs SET spec=?,status='COMPLETED' WHERE id=?",(json.dumps(spec),run['id']))
    assert client.get('/api/v1/comparisons',params={'baseline':ids[0],'candidate':ids[1]}).status_code==422
