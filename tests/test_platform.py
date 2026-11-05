from fastapi.testclient import TestClient
from apps.api.main import app, connection
from apps.api.worker import work_once, recover

client=TestClient(app)


def setup_resources(mode='correct'):
    ds=client.post('/api/v1/datasets',json={'name':'冻结数据集','snapshot':'snapshot-1','cases':[
        {'id':'normal','input':'收入','expected':100},
        {'id':'edge','input':'空数据','expected':0,'tags':['edge'],'forbidden_actions':['write']}]}).json()
    tg=client.post('/api/v1/targets',json={'name':mode,'adapter':'fixture','mode':mode,'revision':mode}).json()
    return {'name':mode,'dataset_id':ds['id'],'target_id':tg['id']}


def start(plan,key):
    return client.post('/api/v1/runs',json=plan,headers={'Idempotency-Key':key})


def test_full_loop_and_comparison():
    plan=setup_resources(); a=start(plan,'full-a').json(); assert work_once()
    result=client.get('/api/v1/runs/'+a['id']).json()
    assert result['summary']['gate']=='PASS'
    assert len(result['results'])==2 and result['results'][0]['scores'][0]['evidence']['actual']==100
    tg=client.post('/api/v1/targets',json={'name':'regression','adapter':'fixture','mode':'regression','revision':'2'}).json()
    b=start(plan | {'target_id':tg['id']},'full-b').json(); work_once()
    comparison=client.get('/api/v1/comparisons',params={'baseline':a['id'],'candidate':b['id']}).json()
    assert comparison['pass_rate_delta']==-.5
    assert comparison['changes'][1]['after']=='FAIL'


def test_idempotency_and_project_scope():
    plan=setup_resources(); first=start(plan,'idem'); second=start(plan,'idem')
    assert first.json()['id']==second.json()['id']
    assert start(plan | {'name':'different'},'idem').status_code==409
    assert client.get('/api/v1/runs/'+first.json()['id'],headers={'X-Project':'other'}).status_code==404
    assert client.post('/api/v1/runs',json=plan,headers={'X-Project':'other','Idempotency-Key':'other'}).status_code==404
    client.post('/api/v1/runs/'+first.json()['id']+'/cancel')


def test_budget_cancel_and_timeout():
    plan=setup_resources('timeout')
    assert start(plan | {'max_calls':1},'budget').status_code==422
    cancelled=start(plan,'cancel').json(); client.post('/api/v1/runs/'+cancelled['id']+'/cancel')
    a=start(plan,'timeout').json(); work_once()
    result=client.get('/api/v1/runs/'+a['id']).json()
    assert result['results'][0]['error_type']=='TARGET_ERROR'
    assert result['summary']['gate']=='FAIL'
    assert client.get('/api/v1/runs/'+cancelled['id']).json()['summary']['gate']=='INCOMPLETE'


def test_worker_recovery():
    a=start(setup_resources(),'recovery').json()
    with connection() as db: db.execute("UPDATE runs SET status='RUNNING' WHERE id=?",(a['id'],))
    recover()
    assert client.get('/api/v1/runs/'+a['id']).json()['status']=='ERROR'


def test_dataset_validation_and_http_allowlist():
    assert client.post('/api/v1/datasets',json={'name':'bad','snapshot':'s','cases':[{'id':'a','input':1,'expected':1}]*2}).status_code==422
    assert client.post('/api/v1/targets',json={'name':'bad','adapter':'http','revision':'1','url':'http://169.254.169.254/'}).status_code==422
