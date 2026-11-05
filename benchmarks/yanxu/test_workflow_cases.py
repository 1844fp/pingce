import json, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.yanxu.scorer import evaluate
class WorkflowCasesTests(unittest.TestCase):
 def test_real_workflow(self):
  from integrations.yanxu.workflow_adapter import execute
  cases=json.loads(Path(__file__).with_name("workflow-cases.v1.json").read_text(encoding="utf-8"))["cases"]
  self.assertGreaterEqual(len(cases),4)
  for case in cases:
   response=execute(case,{})
   scores=evaluate(case,response)
   self.assertFalse(any(s["status"]=="FAIL" for s in scores),(case["id"],response,scores))
   self.assertTrue(any(s["status"]=="NEEDS_REVIEW" for s in scores))
   for field in case["expected"]:
    altered=dict(response);altered["output"]=dict(response["output"]);altered["output"][field]="injected-invalid"
    self.assertTrue(any(s["status"]=="FAIL" for s in evaluate(case,altered)),field)
if __name__=="__main__": unittest.main()
