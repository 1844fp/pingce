import sqlite3
import pytest
from apps.api.migrations import migrate,DIRECTORY,EXPECTED


def test_new_and_legacy_adoption_preserves_data(tmp_path):
    db=sqlite3.connect(tmp_path/'database.db')
    try:
        assert migrate(db)==2
        db.execute("INSERT INTO resources VALUES('existing','p','dataset','name','{}',1)");db.commit()
        assert migrate(db)==2
        db.execute('DROP TABLE audit_events')
        db.execute('DROP TABLE schema_migrations');db.commit()
        assert migrate(db)==2
        assert db.execute('SELECT id FROM resources').fetchone()[0]=='existing'
    finally:db.close()


def test_modified_migration_and_partial_legacy_rejected(tmp_path):
    db=sqlite3.connect(tmp_path/'database.db')
    try:
        migrate(db)
        db.execute("UPDATE schema_migrations SET sha256='modified'");db.commit()
        with pytest.raises(RuntimeError,match='被修改'):migrate(db)
    finally:db.close()
    partial=sqlite3.connect(tmp_path/'partial.db')
    try:
        partial.execute('CREATE TABLE resources(id)');partial.commit()
        with pytest.raises(RuntimeError,match='不完整'):migrate(partial)
        assert not partial.execute("SELECT name FROM sqlite_master WHERE name='schema_migrations'").fetchall()
    finally:partial.close()
