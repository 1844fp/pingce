"""Compare frozen evaluation reports with separate human labels, without model calls.

This is an offline diagnostic, never a release approval or a label writer.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def analyze(report, annotation):
    if report.get('schema_version')!='evaluation-report-v1':raise ValueError('不支持的评测报告格式')
    if annotation.get('schema_version')!='evaluation-calibration-labels-v1':raise ValueError('不支持的标注格式')
    run=report['run'];spec=run['spec']
    if run['status']!='COMPLETED':raise ValueError('仅校准已完成实验')
    if 'run_id' in annotation and (not annotation['run_id'] or annotation['run_id']!=run.get('id')):
        raise ValueError('标注与冻结实验ID不一致')
    if not spec.get('evaluator_hash') or any(annotation.get(k)!=spec.get(k) for k in ('dataset_id','evaluator_hash')):
        raise ValueError('标注必须固定相同数据集ID和评分器摘要')
    cases=spec['dataset']['cases'];repetitions=spec['repetitions']
    expected={(c['id'],n) for c in cases for n in range(repetitions)}
    results=run['results']
    if not expected or len(results)!=len(expected) or {(r['case_id'],r['repetition']) for r in results}!=expected:
        raise ValueError('实验结果不完整或重复')
    labels={}
    for label in annotation['labels']:
        key=(label['case_id'],label['repetition'])
        if key not in expected or key in labels:raise ValueError('标注样本未知或重复')
        if label.get('decision') not in ('PASS','FAIL') or len(label.get('reason','').strip())<5:
            raise ValueError('标注须为PASS/FAIL并包含至少五字的核验依据')
        labels[key]=label
    confusion=Counter();predictions=Counter();disagreements=[]
    for result in results:
        key=(result['case_id'],result['repetition'])
        # Reviews must not become the evaluator prediction: that would make agreement circular.
        prediction=result.get('original_status',result['status'])
        if prediction not in ('PASS','FAIL','ERROR','NEEDS_REVIEW'):raise ValueError('未知原始评分状态')
        if key not in labels:continue
        predictions[prediction]+=1
        decision=labels[key]['decision']
        if prediction in ('PASS','FAIL'):
            confusion[(prediction,decision)]+=1
            if prediction!=decision:
                disagreements.append({'case_id':key[0],'repetition':key[1],'predicted':prediction,'human':decision})
    binary=sum(confusion.values());human_fail=sum(v for (p,h),v in confusion.items() if h=='FAIL')
    false_accept=confusion['PASS','FAIL'];false_reject=confusion['FAIL','PASS']
    annotated=len(labels)
    return {
        'schema_version':'evaluation-calibration-v1','dataset_id':spec['dataset_id'],'evaluator_hash':spec['evaluator_hash'],
        'run_id':run.get('id'),'total':len(expected),'annotated':annotated,'unlabelled':len(expected)-annotated,
        'annotation_coverage':annotated/len(expected),'binary_decisions':binary,
        'binary_coverage':binary/annotated if annotated else None,
        'abstentions':predictions['NEEDS_REVIEW'],'execution_or_scoring_errors':predictions['ERROR'],
        'agreement':(confusion['PASS','PASS']+confusion['FAIL','FAIL'])/binary if binary else None,
        'false_accepts':false_accept,'false_rejects':false_reject,
        'false_accept_rate_on_human_fail':false_accept/human_fail if human_fail else None,
        'confusion':{'predicted_pass_human_pass':confusion['PASS','PASS'],'predicted_pass_human_fail':false_accept,
                     'predicted_fail_human_pass':false_reject,'predicted_fail_human_fail':confusion['FAIL','FAIL']},
        'disagreements':disagreements,'release_approval':False,
        'limits':['描述性统计，无置信界限或自动校准通过结论','原始待复核与错误不当作二分类预测',
                  '标注为用户提供的本地证据，不证明独立标注者身份或研究事实','不改写参考答案、评分或人工复核，不调用模型']}


def output_path(value):
    destination=Path(value)
    if not destination.is_absolute():destination=ROOT/destination
    destination=destination.resolve()
    if not destination.is_relative_to(ROOT):raise ValueError('输出必须位于评测中台根目录')
    if destination.exists():raise ValueError('校准报告不得覆盖已有文件，请使用新文件名')
    destination.parent.mkdir(parents=True,exist_ok=True)
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--labels',required=True,type=Path)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        result=analyze(json.loads(args.report.read_text(encoding='utf-8-sig')),json.loads(args.labels.read_text(encoding='utf-8-sig')))
        destination=output_path(args.output)
        with destination.open('x',encoding='utf-8') as handle:json.dump(result,handle,ensure_ascii=False,indent=2)
        print(json.dumps({'report':str(destination),'annotated':result['annotated'],'release_approval':False},ensure_ascii=False))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'error':str(exc),'release_approval':False},ensure_ascii=False));return 2


if __name__=='__main__':sys.exit(main())
