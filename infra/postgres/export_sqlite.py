"""Read-only SQLite snapshot to validated JSON + PostgreSQL INSERT SQL. No client/network."""
import argparse, json, math, sqlite3
from pathlib import Path
TABLES={
 "resources": "id project kind name body created".split(),
 "runs": "id project name spec status created updated idem digest error".split(),
 "results": "id run_id case_id repetition body".split(),
 "reviews": "id run_id case_id repetition decision reason created".split()}
JSON_FIELDS={"resources":{"body"},"runs":{"spec"},"results":{"body"},"reviews":set()}
def strict_json(text):
 def pairs(items):
  result={}
  for k,v in items:
   if k in result: raise ValueError("duplicate JSON key")
   result[k]=v
  return result
 return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
def snapshot(source):
 source=Path(source).resolve(strict=True)
 db=sqlite3.connect(source.as_uri()+"?mode=ro",uri=True)
 db.row_factory=sqlite3.Row
 try:
  db.execute("BEGIN")
  data={}
  for table,columns in TABLES.items():
   actual=[r[1] for r in db.execute("PRAGMA table_info("+table+")")]
   if actual!=columns:raise ValueError("unsupported schema: "+table)
   rows=[dict(r) for r in db.execute("SELECT * FROM "+table+" ORDER BY id")]
   seen=set()
   for row in rows:
    for col,value in row.items():
     if value is None and not(table=="runs" and col=="error"):raise ValueError("unexpected NULL")
     if value is None:continue
     if col in JSON_FIELDS[table]:row[col]=strict_json(value)
     elif col in {"created","updated"}:
      if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError("invalid epoch")
     elif col=="repetition":
      if type(value)!=int or not -(2**63)<=value<2**63:raise ValueError("invalid repetition")
     elif not isinstance(value,str) or "\x00" in value:raise ValueError("invalid text")
    if row["id"] in seen:raise ValueError("duplicate id")
    seen.add(row["id"])
   data[table]=rows
  ids={r["id"] for r in data["runs"]}
  for table in ("results","reviews"):
   if any(r["run_id"] not in ids for r in data[table]):raise ValueError("orphan run reference")
  for table,cols in (("runs",("project","idem")),("results",("run_id","case_id","repetition"))):
   keys=[tuple(r[c] for c in cols) for r in data[table]]
   if len(keys)!=len(set(keys)):raise ValueError("duplicate business key")
  # PostgreSQL JSONB cannot represent NUL or lone surrogate strings.
  encoded=json.dumps(data,ensure_ascii=False,allow_nan=False)
  if "\\u0000" in encoded.lower():raise ValueError("JSON NUL unsupported")
  encoded.encode("utf-8")
  return {"schema_version":1,"counts":{k:len(v) for k,v in data.items()},"tables":data}
 finally:db.close()
def sql_export(document):
 def literal(value,is_json=False):
  if is_json:value=json.dumps(value,ensure_ascii=False,allow_nan=False)
  if value is None:return "NULL"
  if isinstance(value,(int,float)):return str(value)
  return "'"+value.replace("'","''")+"'"+("::jsonb" if is_json else "")
 lines=["BEGIN;","SET LOCAL standard_conforming_strings = on;"]
 for table,cols in TABLES.items():
  for row in document["tables"][table]:
   lines.append("INSERT INTO "+table+" ("+",".join(cols)+") VALUES ("+",".join(literal(row[c],c in JSON_FIELDS[table]) for c in cols)+");")
 return "\n".join(lines+["COMMIT;",""])
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("source",type=Path);parser.add_argument("destination",type=Path)
 args=parser.parse_args();document=snapshot(args.source)
 args.destination.mkdir(parents=True,exist_ok=True)
 for name in ("snapshot.json","data.sql"):
  if (args.destination/name).exists():raise ValueError("destination artifact already exists")
 (args.destination/"snapshot.json").write_text(json.dumps(document,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
 (args.destination/"data.sql").write_text(sql_export(document),encoding="utf-8")
 print(json.dumps(document["counts"]))
if __name__=="__main__":main()
