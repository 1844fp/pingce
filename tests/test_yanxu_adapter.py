import json
import subprocess
from pathlib import Path
import pytest

ADAPTER = Path(__file__).resolve().parents[1] / 'integrations/yanxu/adapter.mjs'

def call(value, tmp_path):
    result = subprocess.run(['node', str(ADAPTER), '--stdin'], input=json.dumps(value), text=True, encoding="utf-8", capture_output=True, cwd=tmp_path)
    return result

def test_actual_audit(tmp_path):
    result=call({'input':{'operation':'audit','payload':{'bundle':{'claims':[{'id':'c1','kind':'plan','locations':['p1'],'evidence':[]}]},'currentSources':[]}}},tmp_path)
    assert result.returncode == 0, result.stderr
    value=json.loads(result.stdout)
    assert value['output']['issues'][0]['code']=='missing_evidence'
    assert value['trace'][0]['mode']=='real_module_offline'
    assert value['usage']['modelCalls']==0

def test_empty_audit(tmp_path):
    result=call({'input':{'operation':'audit','payload':{'bundle':{'claims':[]},'currentSources':[]}}},tmp_path)
    assert json.loads(result.stdout)['output']['status']=='awaiting_author'

@pytest.mark.parametrize('operation',['shell','../../runtime.mjs','draft'])
def test_reject_arbitrary_operations(operation,tmp_path):
    assert call({'input':{'operation':operation,'payload':{}}},tmp_path).returncode != 0

def test_repair_stale_review(tmp_path):
    result=call({'input':{'operation':'repair','payload':{'paragraphs':{},'sourceVersion':'v2','review':{'sourceVersion':'v1'},'edits':[]}}},tmp_path)
    assert result.returncode != 0
    assert 'stale review' in result.stderr


def test_python_entry_and_manifest(tmp_path):
    import importlib.util
    module_spec=importlib.util.spec_from_file_location('yanxu_adapter_under_test', ADAPTER.with_suffix('.py'))
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    manifest=module.get_manifest()
    case={'input':{'operation':'audit','payload':{'bundle':{'claims':[]},'currentSources':[]}}}
    assert module.execute(case,{'manifest':manifest})['output']['status']=='awaiting_author'
    bad={**manifest,'version':'changed'}
    with pytest.raises(ValueError,match='drift'):
        module.execute(case,{'manifest':bad})

def test_worker_spec_regression(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('yanxu_adapter_worker',ADAPTER.with_suffix('.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case={'input':{'operation':'audit','payload':{'bundle':{'claims':[{'id':'c','kind':'plan','locations':['p'],'evidence':[]}]},'currentSources':[]}}}
    result=module.execute(case,{'target':{'mode':'regression','manifest':module.get_manifest()},'timeout_seconds':5,'scorers':[]})
    assert result['injected_regression'] is True
    assert result['output']['issues']==[]
    assert result['trace'][-1]['status']=='INJECTED'

def test_complete_target_structure(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('yanxu_complete_target',ADAPTER.with_suffix('.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target={'name':'writing offline','adapter':'yanxu-local','revision':1,'url':None,'mode':'correct','manifest':module.get_manifest()}
    case={'input':{'operation':'audit','payload':{'bundle':{'claims':[]},'currentSources':[]}}}
    result=module.execute(case,{'target':target,'timeout_seconds':5})
    assert result['output']['status']=='awaiting_author'
    with pytest.raises(ValueError,match='unsupported adapter'):
        module.execute(case,{'target':{**target,'adapter':'http'}})
    with pytest.raises(ValueError,match='unsupported adapter specification'):
        module.execute(case,{'target':{**target,'command':'arbitrary'}})
