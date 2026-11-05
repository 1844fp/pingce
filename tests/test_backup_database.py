import sqlite3
import pytest
from scripts.backup_database import snapshot


def test_wal_backup_and_safe_restore(tmp_path):
    source=tmp_path/'source.db'; backup=tmp_path/'snapshot.db'; restored=tmp_path/'restored.db'
    with sqlite3.connect(source) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('CREATE TABLE resources(id);CREATE TABLE results(id);CREATE TABLE reviews(reason);CREATE TABLE runs(status,error);')
        db.execute('INSERT INTO reviews VALUES(?)',('保留的复核依据',))
        db.executemany('INSERT INTO runs VALUES(?,NULL)',[('RUNNING',),('QUEUED',),('COMPLETED',)])
        db.commit()
        info=snapshot(source,backup)
        assert info['counts']['reviews']==1
    result=snapshot(backup,restored,restore=True)
    assert result['interrupted_tasks']==2
    with sqlite3.connect(restored) as db:
        assert db.execute('SELECT reason FROM reviews').fetchone()[0]=='保留的复核依据'
        assert db.execute("SELECT count(*) FROM runs WHERE status='ERROR'").fetchone()[0]==2
    with sqlite3.connect(backup) as db:
        assert db.execute("SELECT count(*) FROM runs WHERE status='RUNNING'").fetchone()[0]==1
    with pytest.raises(FileExistsError): snapshot(source,restored)


def test_bad_source_does_not_leave_output(tmp_path):
    source=tmp_path/'wrong.db'; destination=tmp_path/'failed.db'
    with sqlite3.connect(source) as db: db.execute('CREATE TABLE unrelated(id)')
    with pytest.raises(ValueError,match='完整评测'): snapshot(source,destination)
    assert not destination.exists()
