"""Transactional local operation chain; not signed or independently anchored."""
import hashlib
import json
import time
import uuid


def digest(event):
    fields={k:event[k] for k in ('event_id','project','action','resource_id','metadata','created','previous_sha')}
    return hashlib.sha256(json.dumps(fields,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def append(db,project,action,resource_id,metadata=None):
    previous=db.execute('SELECT sha256 FROM audit_events WHERE project=? ORDER BY seq DESC LIMIT 1',(project,)).fetchone()
    event={'event_id':str(uuid.uuid4()),'project':project,'action':action,'resource_id':resource_id,'metadata':json.dumps(metadata or {},ensure_ascii=False,sort_keys=True),'created':time.time(),'previous_sha':previous[0] if previous else ''}
    event['sha256']=digest(event)
    db.execute('INSERT INTO audit_events(event_id,project,action,resource_id,metadata,created,previous_sha,sha256) VALUES(?,?,?,?,?,?,?,?)',tuple(event[k] for k in ('event_id','project','action','resource_id','metadata','created','previous_sha','sha256')))


def read(db,project,limit=100):
    events=[dict(r) for r in db.execute('SELECT * FROM audit_events WHERE project=? ORDER BY seq',(project,))]
    previous='';valid=True
    for event in events:
        if event['previous_sha']!=previous or digest(event)!=event['sha256']:valid=False
        previous=event['sha256']
    return {'chain_valid':valid,'total':len(events),'events':events[-limit:],'limits':'本地一致性链，非签名/实名审计；无法防止有数据库写权限者重算整链或删除尾部'}
