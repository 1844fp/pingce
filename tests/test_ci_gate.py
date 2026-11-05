import copy
from scripts.check_gate import check


def report():
    return {'run':{'status':'COMPLETED','spec':{'target_id':'fixed','dataset':{'cases':[{'id':'one'}]},'repetitions':1},'summary':{'gate':'PASS'},'results':[{'case_id':'one','repetition':0,'status':'PASS','scores':[{'status':'PASS'}]}]}}


def test_gate_complete_and_pinned():
    data=report()
    assert check(data,'fixed')[0]
    assert not check(data,'another')[0]
    for state in ['QUEUED','RUNNING','CANCELLED','ERROR']:
        modified=copy.deepcopy(data); modified['run']['status']=state
        assert not check(modified)[0]
    data['run']['results']*=2
    assert not check(data)[0]


def test_gate_requires_review_and_cannot_override_failure():
    data=report(); row=data['run']['results'][0]
    row['scores']=[{'status':'NEEDS_REVIEW'}]
    assert not check(data)[0]
    row['reviews']=[{'decision':'PASS','reason':'人工已核对合成契约'}]
    assert check(data)[0]
    row['scores'].append({'status':'FAIL'})
    assert not check(data)[0]
