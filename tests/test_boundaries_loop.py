import uuid
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.worker import work_once


def test_real_business_boundary_loop():
    client=TestClient(app)
    template=client.get('/api/v1/templates/yanxu-writing?suite=boundaries')
    assert template.status_code==200,template.text
    ds=client.post('/api/v1/datasets',json=template.json()).json()
    target=client.post('/api/v1/targets',json={'name':'业务边界合成依赖','adapter':'yanxu-boundaries','revision':'boundaries-v1'})
    assert target.status_code==201,target.text
    created=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'真实选题与取消','dataset_id':ds['id'],'target_id':target.json()['id'],'timeout_seconds':15}).json()
    work_once()
    result=client.get('/api/v1/runs/'+created['id']).json()
    assert result['status']=='COMPLETED'
    assert result['summary']['failed']==0,result['results']
    assert result['summary']['needs_review']==2
    assert result['summary']['gate']=='NEEDS_REVIEW'
    outputs={r['input']['operation']:r['output']['output'] for r in result['results']}
    assert outputs['runtime_cancel']['job_status']=='cancelled'
    assert outputs['runtime_cancel']['output_present'] is False
