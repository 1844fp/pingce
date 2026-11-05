import json
import pytest
from apps.api.artifacts import ArtifactStore,ArtifactIntegrityError,MAX_BYTES

def test_roundtrip_and_project_isolation(tmp_path):
    store=ArtifactStore(tmp_path/'store');meta=store.put('a',b'{"ok":true}','application/json')
    assert store.get('a',meta['id'])==(meta,b'{"ok":true}')
    with pytest.raises(FileNotFoundError):store.get('b',meta['id'])
    assert not list((tmp_path/'store').rglob('.pending-*'))

def test_tamper(tmp_path):
    store=ArtifactStore(tmp_path);meta=store.put('a',b'hello','text/plain')
    path=next(tmp_path.rglob(meta['id']+'.json'));value=json.loads(path.read_bytes());value['meta']['mime']='text/html';path.write_text(json.dumps(value))
    with pytest.raises(ArtifactIntegrityError):store.get('a',meta['id'])

def test_limits_and_paths(tmp_path):
    store=ArtifactStore(tmp_path)
    with pytest.raises(ValueError):store.put('a',b'x'*(MAX_BYTES+1),'text/plain')
    with pytest.raises(ValueError):store.get('a','../../outside')
    with pytest.raises(ValueError):store.put('a',b'x','application/x-executable')
    meta=store.put('../project',b'','text/plain');assert store.get('../project',meta['id'])[1]==b''

def test_atomic_failure(tmp_path,monkeypatch):
    import apps.api.artifacts as module
    store=ArtifactStore(tmp_path)
    def fail(*args):raise OSError('injected rename failure')
    monkeypatch.setattr(module.os,'replace',fail)
    with pytest.raises(OSError):store.put('a',b'x','text/plain')
    assert not list(tmp_path.rglob('*.json')) and not list(tmp_path.rglob('.pending-*'))

def test_content_corruption(tmp_path):
    store=ArtifactStore(tmp_path);meta=store.put('a',b'hello','text/plain')
    path=next(tmp_path.rglob(meta['id']+'.json'));value=json.loads(path.read_bytes());value['content']='aGFja2Vk';path.write_text(json.dumps(value))
    with pytest.raises(ArtifactIntegrityError):store.get('a',meta['id'])

def test_exact_limit(tmp_path):
    store=ArtifactStore(tmp_path);content=b'x'*MAX_BYTES;meta=store.put('a',content,'application/octet-stream')
    assert store.get('a',meta['id'])[1]==content

def test_environment_root_override(tmp_path,monkeypatch):
    import importlib.util
    from pathlib import Path
    import apps.api.artifacts as existing
    root=tmp_path/'restored-artifacts';monkeypatch.setenv('EVAL_ARTIFACT_ROOT',str(root))
    spec=importlib.util.spec_from_file_location('isolated_artifacts_env',Path(existing.__file__))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    meta=module.put('restore',b'restored','text/plain')
    assert module._DEFAULT.root==root.absolute()
    assert module.get('restore',meta['id'])[1]==b'restored'
