"""Fail closed on local evaluation reports. Does not deploy or approve reviews."""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def check(report, target_id=None):
    run=report.get('run',{})
    if run.get('status')!='COMPLETED': return False,'运行未完成'
    if target_id and run.get('spec',{}).get('target_id')!=target_id: return False,'被测目标版本不匹配'
    cases=run.get('spec',{}).get('dataset',{}).get('cases',[])
    repetitions=run.get('spec',{}).get('repetitions',1)
    expected={(c['id'],n) for c in cases for n in range(repetitions)}
    results=run.get('results',[])
    actual={(r.get('case_id'),r.get('repetition')) for r in results}
    if not expected or actual!=expected or len(results)!=len(expected): return False,'样本不完整或重复'
    for result in results:
        if result.get('status')!='PASS': return False,'存在失败、错误或待复核项'
        scores=result.get('scores',[])
        if not scores or any(s.get('status') not in ('PASS','NOT_APPLICABLE','NEEDS_REVIEW') for s in scores): return False,'评分缺失或确定性失败'
        if any(s.get('status')=='NEEDS_REVIEW' for s in scores):
            reviews=result.get('reviews',[])
            if not reviews or reviews[-1].get('decision')!='PASS' or len(reviews[-1].get('reason','').strip())<5:
                return False,'缺少人工复核通过依据'
    if run.get('summary',{}).get('gate')!='PASS': return False,'门禁未通过'
    return True,'所有预期样本通过；仅代表指定评测范围'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--report',type=Path)
    source.add_argument('--run-id')
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--project',default='default')
    parser.add_argument('--target-id',help='Require the exact immutable target ID')
    args=parser.parse_args()
    try:
        if args.report:
            report=json.loads(args.report.read_text(encoding='utf-8'))
        else:
            import uuid
            rid=str(uuid.UUID(args.run_id))
            token=os.getenv('EVAL_CLIENT_TOKEN','')
            request=urllib.request.Request(args.url.rstrip('/')+f'/api/v1/runs/{rid}/report',headers={'X-Project':args.project,**({'Authorization':'Bearer '+token} if token else {})})
            with urllib.request.urlopen(request,timeout=15) as response: report=json.load(response)
        ok,reason=check(report,args.target_id)
        print(json.dumps({'allowed':ok,'reason':reason},ensure_ascii=False))
        return 0 if ok else 1
    except Exception as exc:
        print(json.dumps({'allowed':False,'reason':f'无法验证报告: {type(exc).__name__}'},ensure_ascii=False))
        return 2


if __name__=='__main__': sys.exit(main())
