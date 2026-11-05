from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.worker import work_once
import uuid


def test_real_workflow_control_plane():
    client=TestClient(app)
    template=client.get('/api/v1/templates/yanxu-writing?suite=workflow')
    assert template.status_code==200,template.text
    ds=client.post('/api/v1/datasets',json=template.json()).json()
    target=client.post('/api/v1/targets',json={'name':'真实编排合成依赖','adapter':'yanxu-workflow','mode':'correct','revision':'workflow-v1'})
    assert target.status_code==201,target.text
    assert client.post('/api/v1/targets',json={'name':'禁止注入','adapter':'yanxu-workflow','mode':'regression','revision':'v1'}).status_code==422
    run=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'工作流闭环','dataset_id':ds['id'],'target_id':target.json()['id'],'timeout_seconds':15}).json()
    assert work_once()
    result=client.get('/api/v1/runs/'+run['id']).json()
    assert result['status']=='COMPLETED',result
    assert result['summary']['failed']==0,result['results']
    assert result['summary']['needs_review']==4
    assert result['summary']['gate']=='NEEDS_REVIEW'
    assert all(r['output']['usage']['modelCalls']==0 for r in result['results'])
