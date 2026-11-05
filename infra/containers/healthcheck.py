"""Linux container readiness; worker lock presence is not progress monitoring."""
import os
from pathlib import Path
import sqlite3
import sys
import urllib.request

if sys.argv[1] == 'api':
    with urllib.request.urlopen('http://127.0.0.1:8765/api/v1/health', timeout=3) as response:
        assert response.status == 200
else:
    import fcntl
    assert b'apps.api.worker' in Path('/proc/1/cmdline').read_bytes() or any(
        b'apps.api.worker' in p.read_bytes() for p in Path('/proc').glob('[0-9]*/cmdline') if p.exists())
    database = Path(os.environ['EVAL_DB'])
    with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True, timeout=2) as connection:
        connection.execute('SELECT 1 FROM runs LIMIT 1').fetchall()
    with open(str(database)+'.worker.lock', 'rb') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise RuntimeError('worker lock not held')
