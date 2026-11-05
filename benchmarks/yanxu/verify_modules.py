import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from integrations.yanxu.adapter import execute
from benchmarks.yanxu.scorer import evaluate

def verify():
 cases=json.loads(Path(__file__).with_name("module-cases.v1.json").read_text(encoding="utf-8"))["cases"]
 summary={}
 for mode in ("correct","regression"):
  failed=[]
  for case in cases:
   scores=evaluate(case,execute(case,{"mode":mode}))
   has_failure=any(s["status"]=="FAIL" for s in scores)
   assert any(s["status"]=="NEEDS_REVIEW" for s in scores), scores
   if has_failure: failed.append(case["id"])
   if mode=="correct": assert not has_failure,(case["id"],scores)
  summary[mode]={"total":len(cases),"failed":failed,"needs_review":len(cases)}
 assert len(summary["regression"]["failed"])>=5,summary
 return summary
if __name__=="__main__": print(json.dumps(verify(),ensure_ascii=False,indent=2))
