import uuid
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.worker import work_once


def test_graph_control_plane_and_provenance():
    client=TestClient(app)
    template=client.get('/api/v1/templates/yanxu-writing?suite=knowledge')
    assert template.status_code==200,template.text
    ds=client.post('/api/v1/datasets',json=template.json()).json()
    target=client.post('/api/v1/targets',json={'name':'真实图谱合成SQLite','adapter':'yanxu-knowledge','revision':'knowledge-v1'})
    assert target.status_code==201,target.text
    run=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'来源追溯闭环','dataset_id':ds['id'],'target_id':target.json()['id']}).json()
    work_once()
    result=client.get('/api/v1/runs/'+run['id']).json()
    assert result['status']=='COMPLETED'
    assert result['summary']['failed']==0,result['results']
    assert result['summary']['needs_review']==3
    assert result['summary']['gate']=='NEEDS_REVIEW'
    outputs={r['input']['operation']:r['output']['output'] for r in result['results']}
    assert outputs['navigation_trace']['review']=='unreviewed_navigation'
    assert outputs['navigation_trace']['verification']=='navigation_not_fact_verified'
    assert outputs['stale_source']['edge_count']==0
    assert outputs['stale_source']['trace_error']
    assert outputs['empty_lookup']['trace_text'] is None
