import threading
import uuid
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api import worker
from apps.api.worker_lock import exclusive_worker


def test_worker_guard_rejects_second_and_releases(tmp_path):
    path=tmp_path/'isolated.db'
    with exclusive_worker(path):
        with pytest.raises(RuntimeError,match='已有 Worker'):
            with exclusive_worker(path): pass
    with exclusive_worker(path): pass


def test_cancel_during_target_discards_late_result(monkeypatch):
    client=TestClient(app)
    ds=client.post('/api/v1/datasets',json={'name':'取消验收','snapshot':'synthetic','cases':[{'id':str(i),'input':i,'expected':i} for i in range(2)]}).json()
    target=client.post('/api/v1/targets',json={'name':'受控慢目标','adapter':'fixture','revision':'1'}).json()
    rid=client.post('/api/v1/runs',headers={'Idempotency-Key':str(uuid.uuid4())},json={'name':'运行中取消','dataset_id':ds['id'],'target_id':target['id']}).json()['id']
    entered=threading.Event(); release=threading.Event(); calls=[]
    def blocked(case,spec):
        calls.append(case['id']); entered.set()
        if not release.wait(5): raise TimeoutError('test release not received')
        return {'output':case['expected'],'actions':[]}
    monkeypatch.setattr(worker,'execute',blocked)
    thread=threading.Thread(target=worker.work_once)
    thread.start()
    try:
        assert entered.wait(5)
        assert client.post(f'/api/v1/runs/{rid}/cancel').json()['status']=='CANCELLED'
    finally: release.set(); thread.join(5)
    assert not thread.is_alive()
    result=client.get(f'/api/v1/runs/{rid}').json()
    assert result['status']=='CANCELLED' and result['summary']['gate']=='INCOMPLETE'
    assert result['results']==[] and len(calls)==1
