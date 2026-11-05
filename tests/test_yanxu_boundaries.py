import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'integrations/yanxu/boundaries_adapter.py'
S=importlib.util.spec_from_file_location('boundaries_test',P)
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
@pytest.mark.parametrize('operation',M.OPERATIONS)
def test_boundary(operation):
    result=M.execute({'input':{'operation':operation}},{'target':{'adapter':'yanxu-boundaries','manifest':M.get_manifest()},'timeout_seconds':15})
    assert all(result['output']['checks'].values()),result
    if operation=='runtime_cancel':
        output=result['output']
        assert (output['cancel_http_status'],output['job_status'],output['run_status'],output['output_present'],output['fetch_calls'])==(200,'cancelled','interrupted',False,1)
    else:
        assert result['output']['quality_status']=='needs_scope'
        assert 'data unavailable' in result['output']['handoff_error']
