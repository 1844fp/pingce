"""Set isolation before any application import during test collection."""
import os
import tempfile

os.environ['EVAL_DB']=os.path.join(tempfile.mkdtemp(prefix='eval-tests-'),'test.db')
