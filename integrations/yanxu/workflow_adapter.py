import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path('E:/AI/codex/writing-site')
HERE=Path(__file__).parent
OPERATIONS=('references','missing_material','resume_parameters_changed','resume_input_changed')
def get_manifest():
    paths=list((ROOT/'src').glob('*.mjs'))+[ROOT/'package-lock.json',HERE/'workflow_adapter.py',HERE/'workflow_adapter.mjs']
    return {'schema':1,'version':'workflow-offline-v1','files':{('src/'+p.name if p.parent==ROOT/'src' else p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
def execute(case,spec):
    target=spec.get('target',spec)
    if any(k not in {'name','adapter','revision','url','mode','manifest','version'} for k in target):raise ValueError('unknown target configuration')
    if target.get('adapter','yanxu-workflow')!='yanxu-workflow' or target.get('mode','correct')!='correct':raise ValueError('unsupported target')
    if target.get('version','workflow-offline-v1')!='workflow-offline-v1':raise ValueError('unsupported version')
    value=case.get('input',{})
    if set(value)!={'operation'} or value['operation'] not in OPERATIONS:raise ValueError('fixed synthetic scenarios only')
    before=get_manifest()
    if target.get('manifest',before)!=before:raise ValueError('workflow source drift')
    timeout=spec.get('timeout_seconds',15)
    if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 0<timeout<=120:raise ValueError('invalid timeout')
    result=subprocess.run(['node',str(HERE/'workflow_adapter.mjs')],input=json.dumps({'input':value}),text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if result.returncode:raise ValueError('workflow execution failed: '+result.stderr[-1200:])
    if get_manifest()!=before:raise ValueError('workflow changed during execution')
    response=json.loads(result.stdout)
    response['trace'].append({'name':'manifest','status':'OK','manifest':before})
    return response
