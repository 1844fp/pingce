"""Local evaluation control plane. Run one worker process only."""
import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from apps.api.audit import append as audit_append, read as audit_read

DB = os.getenv('EVAL_DB', str(Path(__file__).resolve().parents[2] / 'evaluation.db'))
app = FastAPI(title='衡尺评测 API', version='0.1.0')


@app.middleware('http')
async def service_access(request: Request, call_next):
    if request.url.path.startswith('/api/v1/') and request.url.path!='/api/v1/health':
        from apps.api.access import authorize
        status,detail=authorize(request.headers.get('authorization'),request.headers.get('x-project','default'),request.method not in ('GET','HEAD','OPTIONS'))
        if status!=200:
            return JSONResponse({'detail':detail},status_code=status,headers={'WWW-Authenticate':'Bearer'} if status==401 else {})
    return await call_next(request)


@contextmanager
def connection():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init():
    with connection() as db:
        db.execute('PRAGMA journal_mode=WAL')
        from apps.api.migrations import migrate
        migrate(db)


init()


class Case(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    input: Any
    expected: Any
    forbidden_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    evaluation: Literal['exact', 'yanxu-writing-v1'] = 'exact'


class Dataset(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cases: list[Case] = Field(min_length=1, max_length=500)
    snapshot: str = Field(min_length=1, max_length=200)


class Target(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    adapter: Literal['fixture', 'http', 'yanxu-local', 'yanxu-workflow', 'yanxu-lifecycle', 'yanxu-boundaries', 'yanxu-knowledge']
    mode: Literal['correct', 'regression', 'timeout'] = 'correct'
    url: str | None = None
    revision: str = Field(min_length=1, max_length=200)


class Plan(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dataset_id: str
    target_id: str
    repetitions: int = Field(default=1, ge=1, le=5)
    timeout_seconds: float = Field(default=5, ge=.1, le=60)
    max_calls: int = Field(default=100, ge=1, le=2500)


def resource(db, rid, project, kind):
    row = db.execute('SELECT * FROM resources WHERE id=? AND project=? AND kind=?', (rid,project,kind)).fetchone()
    if not row:
        raise HTTPException(404, '资源不存在或不属于当前项目')
    return dict(row) | {'body':json.loads(row['body'])}


def save_resource(kind, name, body, project):
    if len(json.dumps(body)) > 2_000_000:
        raise HTTPException(413,'资源超过 2MB 限制')
    rid = str(uuid.uuid4())
    with connection() as db:
        db.execute('INSERT INTO resources VALUES(?,?,?,?,?,?)',(rid,project,kind,name,json.dumps(body,ensure_ascii=False),time.time()))
        audit_append(db,project,kind+'.created',rid,{'kind':kind})
    return {'id':rid,'name':name,'body':body}


@app.get('/api/v1/health')
def health():
    return {'status':'ok','mode':'local-single-user','scorer':'rules-v1'}


@app.post('/api/v1/datasets', status_code=201)
def dataset(data: Dataset, x_project: str = Header(default='default')):
    if len({c.id for c in data.cases}) != len(data.cases):
        raise HTTPException(422,'样本 ID 不能重复')
    return save_resource('dataset',data.name,data.model_dump(),x_project)


@app.post('/api/v1/targets', status_code=201)
def target(data: Target, x_project: str = Header(default='default')):
    if data.adapter == 'http':
        parsed = urlparse(data.url or '')
        allowed = os.getenv('EVAL_ALLOWED_HOSTS','').split(',')
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.hostname not in allowed or parsed.username or parsed.password:
            raise HTTPException(422,'HTTP 目标须使用服务端 EVAL_ALLOWED_HOSTS 中的主机，不允许 URL 凭证')
    body=data.model_dump()
    if data.adapter in ('yanxu-local','yanxu-workflow','yanxu-lifecycle','yanxu-boundaries','yanxu-knowledge'):
        if data.adapter!='yanxu-local' and data.mode!='correct': raise HTTPException(422,'工作流适配器仅支持真实离线编排')
        if data.mode=='timeout': raise HTTPException(422,'写作模块仅支持真实执行或明确标记的回归注入')
        try:
            if data.adapter=='yanxu-knowledge':
                from integrations.yanxu.knowledge_adapter import get_manifest
            elif data.adapter=='yanxu-boundaries':
                from integrations.yanxu.boundaries_adapter import get_manifest
            elif data.adapter=='yanxu-lifecycle':
                from integrations.yanxu.lifecycle_adapter import get_manifest
            elif data.adapter=='yanxu-workflow':
                from integrations.yanxu.workflow_adapter import get_manifest
            else:
                from integrations.yanxu.adapter import get_manifest
            body['manifest']=get_manifest()
        except Exception as exc:
            raise HTTPException(503,f'写作模块版本不可用：{type(exc).__name__}') from exc
    return save_resource('target',data.name,body,x_project)


@app.get('/api/v1/templates/yanxu-writing')
def writing_template(suite: Literal['modules','workflow','lifecycle','boundaries','knowledge']='modules'):
    filename={'modules':'module-cases.v1.json','workflow':'workflow-cases.v1.json','lifecycle':'lifecycle-cases.v1.json','boundaries':'boundaries-cases.v1.json','knowledge':'knowledge-cases.v1.json'}[suite]
    path=Path(__file__).resolve().parents[2]/'benchmarks'/'yanxu'/filename
    if not path.exists(): raise HTTPException(503,'写作模块用例尚未就绪')
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    return Dataset.model_validate(data).model_dump()


def evaluator_hash():
    path=Path(__file__).resolve().parents[2]/'benchmarks'/'yanxu'/'scorer.py'
    return hashlib.sha256(path.read_bytes()).hexdigest()


@app.get('/api/v1/resources/{kind}')
def resources(kind: Literal['dataset','target'], x_project: str = Header(default='default')):
    with connection() as db:
        return [dict(r) | {'body':json.loads(r['body'])} for r in db.execute('SELECT * FROM resources WHERE project=? AND kind=? ORDER BY created DESC',(x_project,kind))]


@app.post('/api/v1/runs', status_code=201)
def create_run(plan: Plan, idempotency_key: str = Header(min_length=1,max_length=200), x_project: str = Header(default='default')):
    digest = hashlib.sha256(plan.model_dump_json().encode()).hexdigest()
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT * FROM runs WHERE project=? AND idem=?',(x_project,idempotency_key)).fetchone()
        if existing:
            if existing['digest'] != digest:
                raise HTTPException(409,'幂等键已用于其他请求')
            return run_view(db,existing)
        ds=resource(db,plan.dataset_id,x_project,'dataset')
        tg=resource(db,plan.target_id,x_project,'target')
        if len(ds['body']['cases'])*plan.repetitions > plan.max_calls:
            raise HTTPException(422,'样本数量乘重复次数超过调用预算')
        is_writing=any(c.get('evaluation')=='yanxu-writing-v1' for c in ds['body']['cases'])
        spec=plan.model_dump() | {'dataset':ds['body'],'target':tg['body'],'evaluator_version':'yanxu-writing-v1' if is_writing else 'rules-v1'}
        if is_writing: spec['evaluator_hash']=evaluator_hash()
        rid=str(uuid.uuid4()); now=time.time()
        db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?)',(rid,x_project,plan.name,json.dumps(spec,ensure_ascii=False),'QUEUED',now,now,idempotency_key,digest,None))
        audit_append(db,x_project,'run.created',rid,{'dataset_id':plan.dataset_id,'target_id':plan.target_id})
        return run_view(db,db.execute('SELECT * FROM runs WHERE id=?',(rid,)).fetchone())


def run_view(db, row):
    data=dict(row); data['spec']=json.loads(data['spec'])
    results=[json.loads(r[0]) for r in db.execute('SELECT body FROM results WHERE run_id=? ORDER BY rowid',(row['id'],))]
    reviews=[dict(r) for r in db.execute('SELECT * FROM reviews WHERE run_id=? ORDER BY created',(row['id'],))]
    for result in results:
        result['original_status']=result['status']
        matching=[r for r in reviews if r['case_id']==result['case_id'] and r['repetition']==result['repetition']]
        result['reviews']=matching
        if result['status']=='NEEDS_REVIEW' and matching:
            result['status']=matching[-1]['decision']
    total=len(data['spec']['dataset']['cases'])*data['spec']['repetitions']
    passed=sum(r['status']=='PASS' for r in results)
    data['results']=results
    needs_review=sum(r['status']=='NEEDS_REVIEW' for r in results)
    failed=sum(r['status'] in ('FAIL','ERROR') for r in results)
    gate='INCOMPLETE'
    if data['status']=='COMPLETED':
        gate='FAIL' if failed else ('NEEDS_REVIEW' if needs_review else ('PASS' if passed==total else 'INCOMPLETE'))
    data['summary']={'total':total,'completed':len(results),'passed':passed,'pass_rate':passed/total,'needs_review':needs_review,'failed':failed,'gate':gate}
    return data


class Review(BaseModel):
    case_id: str
    repetition: int = Field(ge=0)
    decision: Literal['PASS','FAIL']
    reason: str = Field(min_length=5,max_length=2000)


@app.post('/api/v1/runs/{rid}/reviews', status_code=201)
def review(rid: str, data: Review, x_project: str = Header(default='default')):
    if len(data.reason.strip())<5: raise HTTPException(422,'复核依据至少需要五个非空白字符')
    with connection() as db:
        row=db.execute('SELECT * FROM runs WHERE id=? AND project=?',(rid,x_project)).fetchone()
        if not row: raise HTTPException(404,'运行不存在')
        if row['status']!='COMPLETED': raise HTTPException(409,'请等待实验完成后复核')
        result=db.execute('SELECT body FROM results WHERE run_id=? AND case_id=? AND repetition=?',(rid,data.case_id,data.repetition)).fetchone()
        if not result: raise HTTPException(404,'样本结果不存在')
        if json.loads(result[0])['status']!='NEEDS_REVIEW': raise HTTPException(409,'仅人工待复核样本可人工裁决；不能覆盖确定性失败')
        db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),rid,data.case_id,data.repetition,data.decision,data.reason.strip(),time.time()))
        audit_append(db,x_project,'review.created',rid,{'case_id':data.case_id,'repetition':data.repetition,'decision':data.decision})
    return run(rid,x_project)


@app.post('/api/v1/runs/{rid}/regression-dataset', status_code=201)
def regression_dataset(rid: str, x_project: str = Header(default='default')):
    data=run(rid,x_project)
    if data['status']!='COMPLETED': raise HTTPException(409,'只从完整实验沉淀回归样本')
    failed={r['case_id'] for r in data['results'] if r['status'] in ('FAIL','ERROR')}
    if not failed: raise HTTPException(409,'没有已确认失败样本；待复核结果请先复核')
    body=dict(data['spec']['dataset'])
    body['name']=data['name']+' · 失败回归集'
    body['cases']=[c for c in body['cases'] if c['id'] in failed]
    body['source_run_id']=rid
    return save_resource('dataset',body['name'],body,x_project)


@app.get('/api/v1/runs/{rid}/report')
def report(rid: str, x_project: str = Header(default='default')):
    data=run(rid,x_project)
    return {'schema_version':'evaluation-report-v1','exported_at':time.time(),'run':data,
            'limits':['本地单用户；复核为本地操作记录，不是已认证签名','离线模块评测不代表真实模型端到端质量']}


@app.get('/api/v1/runs')
def runs(x_project: str = Header(default='default')):
    with connection() as db:
        return [run_view(db,r) for r in db.execute('SELECT * FROM runs WHERE project=? ORDER BY created DESC',(x_project,))]


@app.get('/api/v1/runs/{rid}')
def run(rid: str, x_project: str = Header(default='default')):
    with connection() as db:
        row=db.execute('SELECT * FROM runs WHERE id=? AND project=?',(rid,x_project)).fetchone()
        if not row: raise HTTPException(404,'运行不存在')
        return run_view(db,row)


@app.post('/api/v1/runs/{rid}/cancel')
def cancel(rid: str, x_project: str = Header(default='default')):
    with connection() as db:
        row=db.execute('SELECT * FROM runs WHERE id=? AND project=?',(rid,x_project)).fetchone()
        if not row: raise HTTPException(404,'运行不存在')
        if row['status'] in ('QUEUED','RUNNING'):
            db.execute("UPDATE runs SET status='CANCELLED',updated=? WHERE id=?",(time.time(),rid))
            audit_append(db,x_project,'run.cancelled',rid)
    return run(rid,x_project)


@app.get('/api/v1/comparisons')
def compare(baseline: str, candidate: str, x_project: str = Header(default='default')):
    a=run(baseline,x_project); b=run(candidate,x_project)
    if a['status']!='COMPLETED' or b['status']!='COMPLETED': raise HTTPException(409,'只支持完整实验对比')
    if any(a['spec'].get(k)!=b['spec'].get(k) for k in ('dataset_id','repetitions','evaluator_version','evaluator_hash')):
        raise HTTPException(422,'对比需要相同数据集版本、重复次数和评分器版本')
    index={(r['case_id'],r['repetition']):r for r in a['results']}
    changes=[]
    for r in b['results']:
        old=index[(r['case_id'],r['repetition'])]
        changes.append({'case_id':r['case_id'],'repetition':r['repetition'],'before':old['status'],'after':r['status'],'latency_delta_ms':r['latency_ms']-old['latency_ms']})
    return {'baseline':a['name'],'candidate':b['name'],'pass_rate_delta':b['summary']['pass_rate']-a['summary']['pass_rate'],
            'new_failures':sum(c['before'] not in ('FAIL','ERROR') and c['after'] in ('FAIL','ERROR') for c in changes),
            'resolved_failures':sum(c['before'] in ('FAIL','ERROR') and c['after']=='PASS' for c in changes),
            'baseline_summary':a['summary'],'candidate_summary':b['summary'],'changes':changes}


@app.get('/api/v1/audit')
def audit(limit: int = 100, x_project: str = Header(default='default')):
    if not 1<=limit<=200:raise HTTPException(422,'limit须为1到200')
    with connection() as db:return audit_read(db,x_project,limit)


@app.post('/api/v1/runs/{rid}/archive',status_code=201)
def archive_report(rid: str,x_project: str = Header(default='default')):
    from apps.api.artifacts import put,ArtifactIntegrityError
    document=report(rid,x_project)
    try:
        metadata=put(x_project,json.dumps(document,ensure_ascii=False,sort_keys=True).encode('utf-8'),'application/json')
    except ArtifactIntegrityError as exc:raise HTTPException(409,'产物库完整性校验失败') from exc
    except ValueError as exc:raise HTTPException(422,'报告超过本地产物大小限制') from exc
    with connection() as db:audit_append(db,x_project,'report.archived',metadata['id'],{'run_id':rid,'sha256':metadata['sha256']})
    return metadata


@app.get('/api/v1/artifacts/{artifact_id}')
def download_artifact(artifact_id: str,x_project: str = Header(default='default')):
    from apps.api.artifacts import get,ArtifactIntegrityError
    try:metadata,content=get(x_project,artifact_id)
    except FileNotFoundError as exc:raise HTTPException(404,'产物不存在') from exc
    except ArtifactIntegrityError as exc:raise HTTPException(409,'产物完整性校验失败') from exc
    except ValueError as exc:raise HTTPException(422,'产物标识无效') from exc
    return Response(content,media_type=metadata['mime'],headers={'Content-Disposition':f'attachment; filename="artifact-{artifact_id}"','X-Content-Type-Options':'nosniff','Cache-Control':'no-store','X-Artifact-SHA256':metadata['sha256']})


dist=Path(__file__).resolve().parents[1]/'web'/'dist'
if dist.exists(): app.mount('/',StaticFiles(directory=dist,html=True),name='web')
