import json
from pathlib import Path
import pytest
from scripts.doctor import inspect,write_report,ADAPTERS,BUSINESS_FILES,GRAPH_FILES

def fixture(root):
 root.mkdir();(root/"requirements.txt").write_text("fastapi==1.0\n")
 paths=[root/"apps/web/dist/index.html",root/"apps/web/dist/assets/app.js"]
 for stem in ADAPTERS:
  paths.append(root/"integrations/yanxu"/(stem+".py"))
  if stem!="knowledge_adapter":paths.append(root/"integrations/yanxu"/(stem+".mjs"))
 paths += [root/"business"/x for x in BUSINESS_FILES]+[root/"graph"/x for x in GRAPH_FILES]
 for path in paths:path.parent.mkdir(parents=True,exist_ok=True);path.write_text("synthetic")
 return lambda **kw:inspect(root,root/"business",root/"graph",version=kw.get("version",lambda _:"1.0"),which=lambda _:"synthetic-node")
def test_success_and_missing(tmp_path):
 root=tmp_path/"project";check=fixture(root)
 assert check()["status"]=="PASS"
 (root/"integrations/yanxu/adapter.py").unlink()
 result=check();assert result["status"]=="FAIL"
 assert any(c["name"]=="adapter:adapter.py" and c["status"]=="FAIL" for c in result["checks"])
def test_version_and_report_boundary(tmp_path):
 root=tmp_path/"project";check=fixture(root)
 assert check(version=lambda _:"wrong")["status"]=="FAIL"
 with pytest.raises(ValueError):write_report(check(),tmp_path/"outside.json",root)
 target=root/"reports/doctor.json";write_report(check(),target,root)
 assert json.loads(target.read_text(encoding="utf-8"))["api_health"]=="NOT_CHECKED"
 assert not (tmp_path/"outside.json").exists()
