from contextlib import closing
import hashlib
from types import ModuleType
import json
from pathlib import Path
import sqlite3
import tempfile
ROOT=Path(__file__).resolve().parents[2]
GRAPH=Path('E:/AI/codex/agent-team/deliveries/knowledge-graph-20261102/graph.py')
SERVER=Path('E:/AI/codex/agent-team/mcp/knowledge_server.py')
OPERATIONS=('navigation_trace','stale_source','empty_lookup')
def get_manifest():
    return {'schema':1,'version':'knowledge-offline-v1','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [GRAPH,SERVER,Path(__file__)]}}
def execute(case,spec):
    target=spec.get('target',spec)
    if set(target)-{'name','adapter','revision','url','mode','manifest','version'}:raise ValueError('unknown target configuration')
    if target.get('adapter','yanxu-knowledge')!='yanxu-knowledge' or target.get('mode','correct')!='correct' or target.get('version','knowledge-offline-v1')!='knowledge-offline-v1':raise ValueError('unsupported target')
    value=case.get('input',{})
    if set(value)!={'operation'} or value['operation'] not in OPERATIONS:raise ValueError('fixed synthetic scenarios only')
    before=get_manifest()
    if target.get('manifest',before)!=before:raise ValueError('knowledge source drift')
    timeout=spec.get('timeout_seconds',15)
    if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 0<timeout<=120:raise ValueError('invalid timeout')
    module=ModuleType('yanxu_isolated_graph')
    module.__file__=str(GRAPH)
    exec(compile(GRAPH.read_bytes(),str(GRAPH),'exec'),module.__dict__)
    work=ROOT/'work';work.mkdir(exist_ok=True)
    operation=value['operation']
    with tempfile.TemporaryDirectory(prefix='knowledge-synthetic-',dir=work) as folder:
        source=Path(folder)/'source.sqlite';sidecar=Path(folder)/'graph.sqlite'
        text='SYNTHETIC ONLY 数据资产 数据治理 '+('合成导航测试内容，不代表真实论文。'*4)
        with closing(sqlite3.connect(source)) as c:
            c.executescript('CREATE TABLE docs(doc_id TEXT,title TEXT,text TEXT);CREATE TABLE docs_meta(doc_id TEXT,meta TEXT);CREATE TABLE chunks(doc_id TEXT,idx INTEGER,text TEXT,page INTEGER,page_end INTEGER);')
            c.execute('INSERT INTO docs VALUES(?,?,?)',('synthetic-doc','SYNTHETIC TITLE',text))
            c.execute('INSERT INTO docs_meta VALUES(?,?)',('synthetic-doc','{}'))
            c.execute('INSERT INTO chunks VALUES(?,?,?,?,?)',('synthetic-doc',0,text,7,7))
            c.commit()
        initial=hashlib.sha256(source.read_bytes()).hexdigest()
        module.build(source,sidecar,'synthetic-only')
        graph=module.Graph(source,sidecar,'synthetic-only',allowed_documents=['synthetic-doc'])
        edges=graph.graph_lookup('数据资产')['edges'];edge=edges[0]
        trace=None;trace_error=None
        if operation=='stale_source':
            with closing(sqlite3.connect(source)) as c:c.execute('UPDATE docs SET text=?',('CHANGED SYNTHETIC',));c.commit()
        result=graph.graph_lookup('NO MATCH XYZ' if operation=='empty_lookup' else '数据资产')
        if operation!='empty_lookup':
            try:trace=graph.trace_source(edge['id'],edge['source_sha'],edge['chunk_sha'])
            except ValueError as error:trace_error=str(error)
        output={'scenario':operation,'edge_count':len(result['edges']),'review':trace['review'] if trace else None,'verification':trace['verification'] if trace else None,'doc_id':trace['doc_id'] if trace else None,'page':trace['page'] if trace else None,'trace_text':trace['text'] if trace else None,'trace_error':trace_error,'fallback':result['fallback'],'source_unchanged':initial==hashlib.sha256(source.read_bytes()).hexdigest()}
    if get_manifest()!=before:raise ValueError('knowledge changed during execution')
    return {'output':output,'actions':['execute_synthetic_graph'],'trace':[{'name':operation,'status':'OK','mode':'real_graph_synthetic_sqlite','manifest':before}],'usage':{'cost':0,'currency':'USD','modelCalls':0}}



