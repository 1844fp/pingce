"""Actual module → queue → scorer → review → gate → regression dataset."""
from fastapi.testclient import TestClient
from apps.api.main import app, connection
from apps.api.worker import work_once
import json
import uuid

client=TestClient(app)


def post_run(dataset,target):
    response=client.post('/api/v1/runs',json={'name':'写作闭环验证','dataset_id':dataset,'target_id':target},headers={'Idempotency-Key':str(uuid.uuid4())})
    assert response.status_code==201,response.text
    rid=response.json()['id']
    assert work_once()
    return client.get('/api/v1/runs/'+rid).json()


def test_writing_review_regression_and_report():
    template=client.get('/api/v1/templates/yanxu-writing')
    assert template.status_code==200,template.text
    data=client.post('/api/v1/datasets',json=template.json()).json()
    target=client.post('/api/v1/targets',json={'name':'实际模块','adapter':'yanxu-local','revision':'offline-v1','mode':'correct'})
    assert target.status_code==201,target.text
    baseline=post_run(data['id'],target.json()['id'])
    assert baseline['status']=='COMPLETED'
    assert baseline['summary']['gate']=='NEEDS_REVIEW',baseline['results']
    assert baseline['summary']['failed']==0
    assert baseline['summary']['needs_review']==8
    first=baseline['results'][0]
    review=client.post(f"/api/v1/runs/{baseline['id']}/reviews",json={'case_id':first['case_id'],'repetition':0,'decision':'PASS','reason':'测试用例复核流程验证，不代表真实论文质量'})
    assert review.status_code==201,review.text
    assert review.json()['summary']['needs_review']==7
    assert review.json()['results'][0]['original_status']=='NEEDS_REVIEW'
    assert client.post(f"/api/v1/runs/{baseline['id']}/reviews",json={'case_id':first['case_id'],'repetition':0,'decision':'PASS','reason':'     '}).status_code==422
    report=client.get(f"/api/v1/runs/{baseline['id']}/report").json()
    assert report['run']['spec']['target']['manifest']['files']
    assert report['run']['results'][0]['reviews'][0]['reason']
    regression=client.post('/api/v1/targets',json={'name':'注入回归','adapter':'yanxu-local','revision':'offline-v1-injected','mode':'regression'}).json()
    candidate=post_run(data['id'],regression['id'])
    assert candidate['summary']['gate']=='FAIL'
    assert candidate['summary']['failed']>=5
    failed=next(r for r in candidate['results'] if r['status']=='FAIL')
    assert failed['output']['injected_regression'] is True
    assert client.post(f"/api/v1/runs/{candidate['id']}/reviews",json={'case_id':failed['case_id'],'repetition':0,'decision':'PASS','reason':'不能覆盖确定性失败'}).status_code==409
    compare=client.get('/api/v1/comparisons',params={'baseline':baseline['id'],'candidate':candidate['id']})
    assert compare.status_code==200
    assert compare.json()['new_failures']>=5
    assert any(c['after']=='FAIL' for c in compare.json()['changes'])
    regression_ds=client.post(f"/api/v1/runs/{candidate['id']}/regression-dataset").json()
    assert regression_ds['body']['source_run_id']==candidate['id']
    assert len(regression_ds['body']['cases'])==candidate['summary']['failed']
    # Recover the same failed cases with the real, unmutated module, without granting human approval.
    recovered=post_run(regression_ds['id'],target.json()['id'])
    assert recovered['summary']['failed']==0
    assert recovered['summary']['gate']=='NEEDS_REVIEW'
    assert client.get(f"/api/v1/runs/{baseline['id']}/report",headers={'X-Project':'other'}).status_code==404


def test_source_drift_blocks_execution():
    data=client.post('/api/v1/datasets',json=client.get('/api/v1/templates/yanxu-writing').json()).json()
    target=client.post('/api/v1/targets',json={'name':'漂移拒绝','adapter':'yanxu-local','revision':'v1'}).json()
    response=client.post('/api/v1/runs',json={'name':'hash-check','dataset_id':data['id'],'target_id':target['id']},headers={'Idempotency-Key':str(uuid.uuid4())})
    rid=response.json()['id']
    # Mutate only the test DB's frozen hash; never edit actual application source.
    with connection() as db:
        spec=json.loads(db.execute('SELECT spec FROM runs WHERE id=?',(rid,)).fetchone()[0])
        spec['target']['manifest']['version']='intentionally-invalid'
        db.execute('UPDATE runs SET spec=? WHERE id=?',(json.dumps(spec),rid))
    work_once()
    result=client.get('/api/v1/runs/'+rid).json()
    assert result['summary']['gate']=='FAIL'
    assert all(r['error_type']=='TARGET_ERROR' and 'drift' in r['error'] for r in result['results'])
