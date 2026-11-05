import sqlite3,json
from pathlib import Path
import pytest
from infra.postgres.export_sqlite import snapshot,sql_export
DDL=Path(__file__).resolve().parents[1]/"infra/postgres/001_initial.sql"
def fixture(tmp_path):
 p=tmp_path/"synthetic.sqlite"
 with sqlite3.connect(p) as db:
  db.executescript(DDL.read_text(encoding="utf-8"))
  db.execute("INSERT INTO resources VALUES(?,?,?,?,?,?)",("d","p","dataset","O'Reilly",json.dumps({"x":True}),1))
  db.execute("INSERT INTO runs VALUES('r','p','n','{}','completed',1,2,'key','digest',NULL)")
  db.execute("INSERT INTO results VALUES('s','r','c',0,'{}')")
  db.execute("INSERT INTO reviews VALUES('v','r','c',0,'approve','synthetic',3)")
 return p
def test_export(tmp_path):
 p=fixture(tmp_path);before=p.read_bytes();d=snapshot(p)
 assert d["counts"]==dict(resources=1,runs=1,results=1,reviews=1)
 assert d["tables"]["resources"][0]["body"]=={"x":True}
 assert p.read_bytes()==before
 assert "O''Reilly" in sql_export(d) and "::jsonb" in sql_export(d)
 assert json.loads(json.dumps(d))==d
def test_invalid_source(tmp_path):
 p=fixture(tmp_path)
 with sqlite3.connect(p) as db:db.execute("UPDATE resources SET body='invalid'")
 with pytest.raises(ValueError):snapshot(p)
 with sqlite3.connect(p) as db:
  db.execute("UPDATE resources SET body='{}'");db.execute("UPDATE results SET run_id='orphan'")
 with pytest.raises(ValueError,match="orphan"):snapshot(p)
def test_constraints(tmp_path):
 p=fixture(tmp_path)
 with sqlite3.connect(p) as db:
  db.execute("PRAGMA foreign_keys=ON")
  statements=["INSERT INTO runs SELECT 'r2',project,name,spec,status,created,updated,idem,digest,error FROM runs","INSERT INTO results SELECT 's2',run_id,case_id,repetition,body FROM results","INSERT INTO reviews VALUES('v2','orphan','c',0,'approve','reason',0)"]
  for sql in statements:
   with pytest.raises(sqlite3.IntegrityError):db.execute(sql)
  db.execute("INSERT INTO reviews SELECT 'v3',run_id,case_id,repetition,decision,reason,created FROM reviews")
 assert snapshot(p)["counts"]["reviews"]==2
