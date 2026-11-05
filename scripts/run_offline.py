"""Run only fixed local offline targets via the control plane; never approve content."""
import argparse
import json
import os
import time
import uuid
import urllib.request
from urllib.parse import urlparse
from pathlib import Path

SUITES={'modules':'yanxu-local','workflow':'yanxu-workflow','lifecycle':'yanxu-lifecycle','boundaries':'yanxu-boundaries','knowledge':'yanxu-knowledge'}
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',choices=['all',*SUITES],default='all')
    p.add_argument('--url',default='http://127.0.0.1:8765')
    p.add_argument('--project',default='default')
    p.add_argument('--report',type=Path,default=ROOT/'reports/offline-latest.json')
    p.add_argument('--timeout',type=float,default=180)
    args=p.parse_args()
    parsed=urlparse(args.url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.username or parsed.password:
        p.error('仅允许本机HTTP评测服务')
    destination=args.report.resolve()
    if not destination.is_relative_to(ROOT):p.error('报告必须保存于项目根目录内')
    if args.timeout<=0:p.error('timeout必须为正数')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(path,body=None,key=None):
        request=urllib.request.Request(args.url.rstrip('/')+'/api/v1/'+path,
            data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),
            headers={'Content-Type':'application/json','X-Project':args.project,**({'Authorization':'Bearer '+os.environ['EVAL_CLIENT_TOKEN']} if os.getenv('EVAL_CLIENT_TOKEN') else {}),**({'Idempotency-Key':key} if key else {})})
        with opener.open(request,timeout=15) as response:return json.load(response)
    reports=[]; active=None
    try:
        for suite in SUITES if args.suite=='all' else [args.suite]:
            dataset=api('datasets',api('templates/yanxu-writing?suite='+suite))
            target=api('targets',{'name':'离线批量 '+suite,'adapter':SUITES[suite],'revision':'offline-acceptance','mode':'correct'})
            run=api('runs',{'name':'离线批量 '+suite,'dataset_id':dataset['id'],'target_id':target['id'],'timeout_seconds':15,'max_calls':100},str(uuid.uuid4()))
            active=run['id'];deadline=time.monotonic()+args.timeout
            while run['status'] in ('QUEUED','RUNNING'):
                if time.monotonic()>deadline:
                    api('runs/'+active+'/cancel',{});raise TimeoutError('实验超过等待时间，已请求取消')
                time.sleep(.3);run=api('runs/'+active)
            reports.append({'suite':suite,**api('runs/'+active+'/report')});active=None
        result={'schema_version':'offline-batch-v1','project':args.project,'runs':reports,'all_passed':all(r['run']['summary']['gate']=='PASS' for r in reports)}
        code=0 if result['all_passed'] else 1
    except Exception as exc:
        result={'schema_version':'offline-batch-v1','runs':reports,'all_passed':False,'error':f'{type(exc).__name__}: {exc}','active_run_id':active}
        code=2
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(destination),'all_passed':result['all_passed'],'completed_suites':len(reports),'error':result.get('error')},ensure_ascii=False))
    return code


if __name__=='__main__':raise SystemExit(main())
