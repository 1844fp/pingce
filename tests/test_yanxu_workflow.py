import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'integrations/yanxu/workflow_adapter.py'
S=importlib.util.spec_from_file_location('workflow_under_test',P)
M=importlib.util.module_from_spec(S)
S.loader.exec_module(M)
@pytest.mark.parametrize('operation',M.OPERATIONS)
def test_scenario(operation,tmp_path):
    result=M.execute({'input':{'operation':operation}},{'target':{'adapter':'yanxu-workflow','name':'synthetic','revision':1,'url':None,'mode':'correct','manifest':M.get_manifest()},'timeout_seconds':15})
    assert all(result['output']['checks'].values()),result
    assert result['usage']['modelCalls']==0

def test_reject_paths_and_drift():
    with pytest.raises(ValueError):M.execute({'input':{'operation':'references','path':'x'}},{})
    with pytest.raises(ValueError,match='drift'):M.execute({'input':{'operation':'references'}},{'target':{'manifest':{}}})
