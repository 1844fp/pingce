import json, unittest
from pathlib import Path
from scorer import evaluate
class ScorerTests(unittest.TestCase):
 def test_cases_and_mutations(self):
  cases=json.loads(Path(__file__).with_name("cases.v1.json").read_text(encoding="utf-8"))["cases"]
  self.assertGreaterEqual(len(cases),12)
  for c in cases:
   good=evaluate(c,{"output":c["expected"],"actions":[]})
   self.assertFalse(any(s["status"]=="FAIL" for s in good),c["id"])
   self.assertEqual(any(s["metric"]=="writing_quality" for s in good),c["needs_review"])
   self.assertTrue(any(s["status"]=="FAIL" for s in evaluate(c,{"output":{},"actions":[]})))
   for field in c["expected"]:
    bad=dict(c["expected"]);bad[field]="WRONG"
    self.assertTrue(any(s["status"]=="FAIL" for s in evaluate(c,{"output":bad,"actions":[]})))
   self.assertTrue(any(s["status"]=="FAIL" for s in evaluate(c,{"output":c["expected"],"actions":["paid_model"]})))
 def test_no_checks_requires_review(self):
  self.assertEqual(evaluate({},{} )[0]["status"],"NEEDS_REVIEW")
 def test_boolean_not_integer(self):
  self.assertEqual(evaluate({"checks":[{"field":"n","equals":0}]},{"output":{"n":False}})[0]["status"],"FAIL")
if __name__=="__main__": unittest.main()
