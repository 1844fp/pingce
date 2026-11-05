"""Inert local artifacts, separate project namespaces and authenticated envelopes."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import tempfile

MAX_BYTES=10*1024*1024
MIMES={'application/json','text/plain','text/markdown','text/html','application/pdf','application/octet-stream'}
class ArtifactIntegrityError(ValueError):pass

def _safe(path):
    if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
        raise ArtifactIntegrityError('linked artifact paths forbidden')

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')

class ArtifactStore:
    def __init__(self,root):self.root=Path(root).absolute()
    def _key(self):
        self.root.mkdir(parents=True,exist_ok=True);_safe(self.root)
        path=self.root/'.integrity-key';_safe(path)
        try:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:pass
        else:
            with os.fdopen(fd,'wb') as stream:
                stream.write(secrets.token_bytes(32));stream.flush();os.fsync(stream.fileno())
        key=path.read_bytes()
        if len(key)!=32:raise ArtifactIntegrityError('invalid integrity key')
        return key
    def _namespace(self,project):
        if not isinstance(project,str) or not project.strip() or len(project)>200:raise ValueError('invalid project')
        path=self.root/hashlib.sha256(project.encode()).hexdigest();_safe(path)
        return path
    def put(self,project,content,mime):
        if not isinstance(content,bytes) or len(content)>MAX_BYTES:raise ValueError('content must be bytes up to 10 MiB')
        if mime not in MIMES:raise ValueError('unsupported mime')
        directory=self._namespace(project);key=self._key();directory.mkdir(exist_ok=True);_safe(directory)
        identifier=secrets.token_hex(32)
        meta={'id':identifier,'project':project,'mime':mime,'size':len(content),'sha256':hashlib.sha256(content).hexdigest()}
        payload={'meta':meta,'content':base64.b64encode(content).decode('ascii')}
        envelope={**payload,'mac':hmac.new(key,_canonical(payload),hashlib.sha256).hexdigest()}
        fd,name=tempfile.mkstemp(prefix='.pending-',dir=directory)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(_canonical(envelope));stream.flush();os.fsync(stream.fileno())
            os.replace(name,directory/(identifier+'.json'))
        finally:
            if os.path.exists(name):os.unlink(name)
        return meta
    def get(self,project,identifier):
        if not isinstance(identifier,str) or not re.fullmatch('[0-9a-f]{64}',identifier):raise ValueError('invalid artifact id')
        directory=self._namespace(project);_safe(self.root)
        path=directory/(identifier+'.json');_safe(path)
        if not path.exists():raise FileNotFoundError('artifact not found')
        if path.stat().st_size>15*1024*1024:raise ArtifactIntegrityError('oversized envelope')
        try:
            envelope=json.loads(path.read_bytes());payload={'meta':envelope['meta'],'content':envelope['content']}
            expected=hmac.new(self._key(),_canonical(payload),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected,envelope['mac']):raise ValueError('MAC mismatch')
            meta=payload['meta'];content=base64.b64decode(payload['content'],validate=True)
            if meta['id']!=identifier or meta['project']!=project or meta['mime'] not in MIMES or meta['size']!=len(content) or len(content)>MAX_BYTES or meta['sha256']!=hashlib.sha256(content).hexdigest():raise ValueError('metadata mismatch')
        except (ValueError,KeyError,TypeError) as error:raise ArtifactIntegrityError('artifact integrity check failed') from error
        return dict(meta),content

_DEFAULT=ArtifactStore(os.environ.get('EVAL_ARTIFACT_ROOT') or Path(__file__).resolve().parents[2]/'data'/'artifacts')
def put(project,content,mime):return _DEFAULT.put(project,content,mime)
def get(project,identifier):return _DEFAULT.get(project,identifier)

