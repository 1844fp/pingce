"""Durable SQLite queue; start exactly one worker per database."""
import json
import os
import time
import uuid
from urllib.parse import urlparse

import httpx
from apps.api.main import connection, init, evaluator_hash
from apps.api.audit import append as audit_append


def score(case, output):
    if not isinstance(output,dict) or 'output' not in output or not isinstance(output.get('actions',[]),list):
        raise ValueError('目标响应须含 output，actions 必须为数组')
    if case.get('evaluation')=='yanxu-writing-v1':
        from benchmarks.yanxu.scorer import evaluate
        return evaluate(case,output)
    exact=output['output']==case['expected']
    violations=sorted(set(case.get('forbidden_actions',[])) & set(output.get('actions',[])))
    return [
        {'metric':'exact_match','status':'PASS' if exact else 'FAIL','value':int(exact),'reason':'结果与参考值一致' if exact else '结果与参考值不同','evidence':{'expected':case['expected'],'actual':output['output']},'version':'rules-v1'},
        {'metric':'forbidden_actions','status':'FAIL' if violations else 'PASS','value':int(not violations),'reason':'发现禁止动作' if violations else '未观察到禁止动作','evidence':violations,'version':'rules-v1'}]


def execute(case, spec):
    target=spec['target']
    if target['adapter']=='yanxu-knowledge':
        from integrations.yanxu.knowledge_adapter import execute as execute_knowledge
        return execute_knowledge(case,spec)
    if target['adapter']=='yanxu-boundaries':
        from integrations.yanxu.boundaries_adapter import execute as execute_boundaries
        return execute_boundaries(case,spec)
    if target['adapter']=='yanxu-lifecycle':
        from integrations.yanxu.lifecycle_adapter import execute as execute_lifecycle
        return execute_lifecycle(case,spec)
    if target['adapter']=='yanxu-workflow':
        from integrations.yanxu.workflow_adapter import execute as execute_workflow
        return execute_workflow(case,spec)
    if target['adapter']=='yanxu-local':
        from integrations.yanxu.adapter import execute as execute_yanxu
        return execute_yanxu(case,spec)
    if target['adapter']=='fixture':
        if target['mode']=='timeout': raise TimeoutError('可控测试服务模拟超时')
        value=case['expected']
        if target['mode']=='regression' and 'edge' in case.get('tags',[]): value={'error':'模拟版本在边界样本上返回错误'}
        return {'output':value,'actions':['read_data'],'trace':[{'name':'fixture.read_data','status':'OK'}],'usage':{'source':'fixture','cost':0,'currency':'USD'}}
    url=target['url']; host=urlparse(url).hostname
    if host not in os.getenv('EVAL_ALLOWED_HOSTS','').split(','):
        raise ValueError('目标主机不在当前服务端白名单')
    # No redirects, inherited proxies or credentials; this is an isolated test endpoint.
    with httpx.Client(timeout=spec['timeout_seconds'],follow_redirects=False,trust_env=False) as client:
        with client.stream('POST',url,json={'input':case['input'],'context':{'snapshot':spec['dataset']['snapshot'],'case_id':case['id']}}) as response:
            response.raise_for_status()
            body=bytearray()
            for chunk in response.iter_bytes(chunk_size=65536):
                if len(body)+len(chunk)>2_000_000: raise ValueError('目标响应超过 2MB')
                body.extend(chunk)
            return json.loads(body)


def work_once():
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT * FROM runs WHERE status='QUEUED' ORDER BY created LIMIT 1").fetchone()
        if not row: return False
        rid=row['id']; spec=json.loads(row['spec'])
        db.execute("UPDATE runs SET status='RUNNING',updated=? WHERE id=?",(time.time(),rid))
        audit_append(db,row['project'],'run.started',rid)
    try:
        for case in spec['dataset']['cases']:
            for repetition in range(spec['repetitions']):
                with connection() as db:
                    if db.execute('SELECT status FROM runs WHERE id=?',(rid,)).fetchone()[0]!='RUNNING': return True
                start=time.monotonic(); trace_id=str(uuid.uuid4())
                result={'case_id':case['id'],'repetition':repetition,'input':case['input'],'trace_id':trace_id,'output':None,'scores':[]}
                try:
                    output=execute(case,spec)
                    result['output']=output
                    try:
                        if spec.get('evaluator_hash') and evaluator_hash()!=spec['evaluator_hash']:
                            raise ValueError('评分器代码与实验冻结版本不同，请创建新实验')
                        result['scores']=score(case,output)
                        result['status']=aggregate_scores(result['scores'])
                    except Exception as exc:
                        result.update(status='ERROR',error_type='EVALUATOR_ERROR',error=str(exc))
                except Exception as exc:
                    result.update(status='ERROR',error_type='TARGET_ERROR',error=f'{type(exc).__name__}: {exc}')
                result['latency_ms']=round((time.monotonic()-start)*1000,2)
                with connection() as db:
                    if db.execute('SELECT status FROM runs WHERE id=?',(rid,)).fetchone()[0]!='RUNNING': return True
                    db.execute('INSERT INTO results VALUES(?,?,?,?,?)',(str(uuid.uuid4()),rid,case['id'],repetition,json.dumps(result,ensure_ascii=False)))
                    db.execute('UPDATE runs SET updated=? WHERE id=?',(time.time(),rid))
        with connection() as db:
            changed=db.execute("UPDATE runs SET status='COMPLETED',updated=? WHERE id=? AND status='RUNNING'",(time.time(),rid)).rowcount
            if changed:audit_append(db,row['project'],'run.completed',rid)
    except Exception as exc:
        with connection() as db:
            changed=db.execute("UPDATE runs SET status='ERROR',error=?,updated=? WHERE id=? AND status='RUNNING'",(str(exc),time.time(),rid)).rowcount
            if changed:audit_append(db,row['project'],'run.error',rid)
    return True


def aggregate_scores(scores):
    if not scores or any(s.get('status') not in ('PASS','FAIL','ERROR','NEEDS_REVIEW','NOT_APPLICABLE') for s in scores):
        raise ValueError('评分器返回空列表或未知状态')
    states={s['status'] for s in scores}
    if 'ERROR' in states: return 'ERROR'
    if 'FAIL' in states: return 'FAIL'
    if 'NEEDS_REVIEW' in states: return 'NEEDS_REVIEW'
    if states=={'NOT_APPLICABLE'}: return 'NEEDS_REVIEW'
    return 'PASS'


def recover():
    with connection() as db:
        interrupted=db.execute("SELECT id,project FROM runs WHERE status='RUNNING'").fetchall()
        db.execute("UPDATE runs SET status='ERROR',error='Worker 中断；请使用新幂等键新建实验，未自动重放请求',updated=? WHERE status='RUNNING'",(time.time(),))
        for row in interrupted:audit_append(db,row['project'],'run.interrupted',row['id'])


if __name__=='__main__':
    from apps.api.main import DB
    from apps.api.worker_lock import exclusive_worker
    with exclusive_worker(DB):
        init(); recover()
        print('Evaluation worker ready. Single worker enforced.',flush=True)
        while True:
            if not work_once(): time.sleep(.5)
