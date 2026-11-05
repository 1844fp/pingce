import unittest
from verify_modules import verify
class ModuleRegressionTests(unittest.TestCase):
 def test_real_adapter_modes(self):
  result=verify()
  self.assertEqual(result["correct"]["failed"],[])
  self.assertGreaterEqual(len(result["regression"]["failed"]),5)
  self.assertIn("real-stale-hash",result["regression"]["failed"])
  self.assertEqual(result["correct"]["needs_review"],8)
if __name__=="__main__": unittest.main()
