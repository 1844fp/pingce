"""Read-only local prerequisite checks. Never imports API or starts services."""
import argparse,importlib.metadata,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUSINESS=Path("E:/AI/codex/writing-site")
GRAPH=Path("E:/AI/codex/agent-team")
ADAPTERS=("adapter","workflow_adapter","lifecycle_adapter","boundaries_adapter","knowledge_adapter")
BUSINESS_FILES=("src/writing-evidence.mjs","src/workflow.mjs","src/research-audit.mjs","src/topic-contract.mjs","src/topic-quality.mjs","src/runtime.mjs","src/core.mjs","src/graph-engine.mjs","package-lock.json","node_modules/@langchain/langgraph/package.json")
GRAPH_FILES=("deliveries/knowledge-graph-20261102/graph.py","mcp/knowledge_server.py")
def inspect(root=ROOT,business=BUSINESS,graph=GRAPH,version=importlib.metadata.version,which=shutil.which):
 root=Path(root);checks=[]
 def add(name,ok,detail):checks.append(dict(name=name,status="PASS" if ok else "FAIL",detail=detail))
 add("python",sys.version_info>=(3,11),"Python >=3.11")
 req=root/"requirements.txt"
 add("requirements",req.is_file(),str(req))
 if req.is_file():
  for line in req.read_text(encoding="utf-8-sig").splitlines():
   line=line.strip()
   if not line or line.startswith("#"):continue
   if "==" not in line:add("dependency:"+line,False,"unsupported requirement syntax");continue
   name,expected=line.split("==",1)
   try:actual=version(name)
   except importlib.metadata.PackageNotFoundError:actual=None
   add("dependency:"+name,actual==expected,"expected="+expected+" installed="+str(actual))
 add("node",which("node") is not None,"Node executable on PATH; runtime compatibility not executed")
 for stem in ADAPTERS:
  files=[root/"integrations/yanxu"/(stem+".py")]
  if stem!="knowledge_adapter":files.append(root/"integrations/yanxu"/(stem+".mjs"))
  for path in files:add("adapter:"+path.name,path.is_file(),str(path))
 dist=root/"apps/web/dist"
 add("frontend:index",(dist/"index.html").is_file(),str(dist/"index.html"))
 add("frontend:assets",(dist/"assets").is_dir() and any((dist/"assets").glob("*.js")),str(dist/"assets"))
 for base,files in ((Path(business),BUSINESS_FILES),(Path(graph),GRAPH_FILES)):
  for relative in files:
   path=base/relative;add("business:"+relative,path.is_file(),str(path))
 return dict(schema_version="local-doctor-v1",status="PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL",checks=checks,scope="prerequisites only; no model, network, credentials, database or service startup",optional_not_required=["Docker","PostgreSQL","organization SSO"],api_health="NOT_CHECKED")
def write_report(report,destination,root=ROOT):
 root=Path(root).resolve();destination=Path(destination).resolve()
 if not destination.is_relative_to(root):raise ValueError("report must stay within project root")
 destination.parent.mkdir(parents=True,exist_ok=True)
 destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--report",type=Path)
 args=p.parse_args()
 if args.report and not args.report.resolve().is_relative_to(ROOT.resolve()):p.error("report must stay within project root")
 result=inspect()
 if args.report:write_report(result,args.report)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0 if result["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
