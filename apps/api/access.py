"""Optional local service-token scopes; not SSO or user identity federation."""
import hashlib
import hmac
import json
import os
import re


def authorize(authorization, project, write=False):
    raw=os.getenv('EVAL_AUTH_CONFIG','')
    if not raw:return 200,'local'
    try:
        entries=json.loads(raw)
        if not isinstance(entries,list) or not entries:raise ValueError()
        for entry in entries:
            if not re.fullmatch('[0-9a-f]{64}',entry['sha256']) or entry.get('access') not in ('read','write'):
                raise ValueError()
            if not isinstance(entry['projects'],list) or not entry['projects'] or any(not isinstance(p,str) or not p for p in entry['projects']):raise ValueError()
    except (ValueError,KeyError,TypeError):return 503,'访问配置无效'
    if not authorization or not authorization.startswith('Bearer '):return 401,'需要服务访问令牌'
    token=authorization[7:]
    digest=hashlib.sha256(token.encode()).hexdigest()
    matched=next((e for e in entries if hmac.compare_digest(e['sha256'],digest)),None)
    if not matched:return 401,'访问令牌无效'
    if project not in matched['projects'] or write and matched['access']!='write':return 403,'当前令牌没有所需项目或写入权限'
    return 200,'service-token'
