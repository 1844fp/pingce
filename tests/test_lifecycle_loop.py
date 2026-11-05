import uuid
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.worker import work_once


def test_lifecycle_runs_through_control_plane():
    client=TestClient(app)
    response=client.get('/api/v1/templates/yanxu-writing?suite=lifecycle')
    assert response.status_code==200,response.text
    ds=client.post('/api/v1/datasets',json=response.json()).json()
    target=client.post('/api/v1/targets',json={'name':'生命周期合成依赖','adapter':'yanxu-lifecycle','revision':'lifecycle-v1'})
    assert target.status_code==201,target.text
    created=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'零命中与恢复闭环','dataset_id':ds['id'],'target_id':target.json()['id'],'timeout_seconds':15}).json()
    work_once()
    result=client.get('/api/v1/runs/'+created['id']).json()
    assert result['status']=='COMPLETED'
    assert result['summary']['failed']==0,result['results']
    assert result['summary']['needs_review']==2
    assert result['summary']['gate']=='NEEDS_REVIEW'
    outputs={r['case_id']:r['output']['output'] for r in result['results']}
    assert len(outputs)==2
    assert all(o['search_calls']==1 and o['model_calls']==0 for o in outputs.values())
