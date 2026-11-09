import copy
import pytest
from scripts.calibrate_scores import analyze


def inputs():
    states=['PASS','FAIL','NEEDS_REVIEW','ERROR']
    report={'schema_version':'evaluation-report-v1','run':{'id':'synthetic','status':'COMPLETED','spec':{
        'dataset_id':'fixed','evaluator_hash':'a'*64,'repetitions':1,'dataset':{'cases':[{'id':str(i)} for i in range(4)]}},
        'results':[{'case_id':str(i),'repetition':0,'status':state} for i,state in enumerate(states)]}}
    labels={'schema_version':'evaluation-calibration-labels-v1','dataset_id':'fixed','evaluator_hash':'a'*64,'labels':[
        {'case_id':str(i),'repetition':0,'decision':state,'reason':'合成标注核验依据'} for i,state in enumerate(['FAIL','PASS','PASS','FAIL'])]}
    return report,labels


def test_calibration_exposes_false_accept_reject_and_abstention():
    report,labels=inputs();before=copy.deepcopy(report)
    result=analyze(report,labels)
    assert result['false_accepts']==1 and result['false_rejects']==1
    assert result['agreement']==0 and result['binary_coverage']==.5
    assert result['abstentions']==1 and result['execution_or_scoring_errors']==1
    assert result['release_approval'] is False and report==before


def test_reviews_do_not_become_predictions():
    report,labels=inputs();report['run']['results'][2].update(original_status='NEEDS_REVIEW',status='PASS')
    result=analyze(report,labels)
    assert result['abstentions']==1 and result['binary_decisions']==2


def test_empty_labels_are_not_perfect_agreement():
    report,labels=inputs();labels['labels']=[]
    result=analyze(report,labels)
    assert result['agreement'] is None and result['binary_coverage'] is None
    assert result['annotation_coverage']==0


@pytest.mark.parametrize('change',['dataset','hash','run','duplicate','missing','incomplete','reason'])
def test_bad_calibration_input_rejected(change):
    report,labels=inputs()
    if change=='dataset':labels['dataset_id']='other'
    if change=='hash':labels['evaluator_hash']='other'
    if change=='run':labels['run_id']='another-run'
    if change=='duplicate':labels['labels'].append(labels['labels'][0])
    if change=='missing':report['run']['results'].pop()
    if change=='incomplete':report['run']['status']='RUNNING'
    if change=='reason':labels['labels'][0]['reason']='  '
    with pytest.raises(ValueError):analyze(report,labels)
