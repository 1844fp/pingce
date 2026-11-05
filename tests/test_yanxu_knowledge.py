import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'integrations/yanxu/knowledge_adapter.py'
S=importlib.util.spec_from_file_location('knowledge_test',P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
@pytest.mark.parametrize('operation',M.OPERATIONS)
def test_graph(operation):
    o=M.execute({'input':{'operation':operation}},{'target':{'name':'synthetic','adapter':'yanxu-knowledge','revision':1,'url':None,'mode':'correct','manifest':M.get_manifest()}})['output']
    if operation=='navigation_trace':
        assert o['review']=='unreviewed_navigation'
        assert o['verification']=='navigation_not_fact_verified'
        assert (o['doc_id'],o['page'])==('synthetic-doc',7)
        assert o['trace_text'].startswith('SYNTHETIC ONLY')
        assert o['source_unchanged']
    else:
        assert o['edge_count']==0 and o['trace_text'] is None
        if operation=='stale_source':assert 'Source changed' in o['trace_error']
        else:assert o['trace_error'] is None and o['source_unchanged']
def test_reject_drift_and_paths():
    with pytest.raises(ValueError):M.execute({'input':{'operation':'empty_lookup','path':'x'}},{})
    with pytest.raises(ValueError,match='drift'):M.execute({'input':{'operation':'empty_lookup'}},{'target':{'manifest':{}}})
