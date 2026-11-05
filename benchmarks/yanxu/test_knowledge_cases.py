import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.yanxu.scorer import evaluate
class KnowledgeTests(unittest.TestCase):
 def test_real_graph_boundaries(self):
  from integrations.yanxu.knowledge_adapter import execute
  cases=json.loads(Path(__file__).with_name("knowledge-cases.v1.json").read_text(encoding="utf-8"))["cases"]
  self.assertEqual(len(cases),3)
  for case in cases:
   result=execute(case,{})
   scores=evaluate(case,result)
   self.assertFalse(any(s["status"]=="FAIL" for s in scores),(case["id"],scores))
   self.assertTrue(any(s["status"]=="NEEDS_REVIEW" for s in scores))
   self.assertEqual(result["usage"]["modelCalls"],0)
   for field in case["expected"]:
    bad=dict(result);bad["output"]=dict(result["output"]);bad["output"][field]="injected-invalid"
    self.assertTrue(any(s["status"]=="FAIL" for s in evaluate(case,bad)),field)
