"""Fixed offline module bridge. Never imports evaluation storage."""
import hashlib
import json
import subprocess
from pathlib import Path

ADAPTER = Path(__file__).with_name('adapter.mjs')

def get_manifest():
    """Hash only fixed public source files; no configuration or secrets."""
    sources = {
        'writing-evidence.mjs': Path('E:/AI/codex/writing-site/src/writing-evidence.mjs'),
        'workflow.mjs': Path('E:/AI/codex/writing-site/src/workflow.mjs'),
        'research-audit.mjs': Path('E:/AI/codex/writing-site/src/research-audit.mjs'),
        'adapter.mjs': ADAPTER,
        'adapter.py': Path(__file__),
    }
    return {'schema': 1, 'version': 'offline-v1', 'mode': 'real_module_offline',
            'files': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in sources.items()}}


def execute(case, spec):
    """case: {input: {operation, payload}, context?: object}; spec: {}."""
    runtime_spec = spec
    spec = runtime_spec.get('target', runtime_spec)
    timeout = runtime_spec.get('timeout_seconds', 15)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
        raise ValueError('invalid timeout_seconds')
    if spec and any(k not in {'version', 'manifest', 'mode', 'name', 'adapter', 'revision', 'url'} for k in spec):
        raise ValueError('unsupported adapter specification')
    if spec.get('version', 'offline-v1') != 'offline-v1':
        raise ValueError('unsupported adapter version')
    if spec.get('adapter', 'yanxu-local') != 'yanxu-local':
        raise ValueError('unsupported adapter')
    mode = spec.get('mode', 'correct')
    if mode not in {'correct', 'regression'}:
        raise ValueError('unsupported target mode')
    frozen = spec.get('manifest')
    before = get_manifest()
    if frozen is not None and frozen != before:
        raise ValueError('yanxu source manifest drift')
    if not isinstance(case, dict) or not isinstance(case.get('input'), dict):
        raise ValueError('structured input required')
    if case['input'].get('operation') not in {'audit', 'repair'}:
        raise ValueError('unsupported operation')
    request=json.dumps({'input':case['input'],'context':case.get('context',{})},ensure_ascii=False)
    if len(request.encode('utf-8'))>262144:
        raise ValueError('request too large')
    result=subprocess.run(['node',str(ADAPTER),'--stdin'],input=request,text=True,encoding='utf-8',capture_output=True,timeout=timeout,check=False)
    if result.returncode:
        raise ValueError('offline contract execution failed')
    if get_manifest() != before:
        raise ValueError('yanxu source changed during execution')
    response = json.loads(result.stdout)
    response['trace'].append({'name': 'manifest', 'status': 'OK', 'manifest': before})
    if mode == 'regression':
        if isinstance(response['output'], dict) and 'issues' in response['output']:
            response['output']['issues'] = []
        else:
            response['output'] = {'injected_error': True}
        response['injected_regression'] = True
        response['trace'].append({'name': 'regression_injection', 'status': 'INJECTED', 'mode': 'simulation', 'mutation': 'clear issues or replace output'})
    return response



