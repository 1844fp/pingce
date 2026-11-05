import sqlite3
import pytest
from scripts.backup_local import create,restore
from apps.api.artifacts import ArtifactStore
from apps.api.migrations import migrate


def test_local_bundle_preserves_key_and_artifact(tmp_path):
    root=tmp_path/'project';root.mkdir()
    db=sqlite3.connect(root/'evaluation.db');migrate(db);db.close()
    store=ArtifactStore(root/'data/artifacts');meta=store.put('project',b'synthetic report','text/plain')
    backup=tmp_path/'backup';recovered=tmp_path/'recovered'
    create(root,backup);restore(backup,recovered)
    assert ArtifactStore(recovered/'data/artifacts').get('project',meta['id'])[1]==b'synthetic report'
    with pytest.raises(FileExistsError):restore(backup,recovered)
    (backup/'evaluation.db').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):restore(backup,tmp_path/'bad')
