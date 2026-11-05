import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'integrations/yanxu/lifecycle_adapter.py'
S=importlib.util.spec_from_file_location('lifecycle_test_module',P)
M=importlib.util.module_from_spec(S)
S.loader.exec_module(M)
@pytest.mark.parametrize('operation',M.OPERATIONS)
def test_real_lifecycle(operation):
    result=M.execute({'input':{'operation':operation}},{'target':{'adapter':'yanxu-lifecycle','name':'synthetic','revision':1,'url':None,'mode':'correct','manifest':M.get_manifest()},'timeout_seconds':15})
    assert all(result['output']['checks'].values()),result

def test_reject_untrusted_input():
    with pytest.raises(ValueError):M.execute({'input':{'operation':'references_empty','path':'x'}},{})
    with pytest.raises(ValueError,match='drift'):M.execute({'input':{'operation':'references_empty'}},{'target':{'manifest':{}}})

