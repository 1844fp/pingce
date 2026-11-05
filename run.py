"""Start local API and one worker, stop both with Ctrl+C."""
import os
import subprocess
import sys
import time
from pathlib import Path

root=Path(__file__).resolve().parent
os.chdir(root)
children=[]
try:
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    for args in (['-m','uvicorn','apps.api.main:app','--host','127.0.0.1','--port','8765'],['-m','apps.api.worker']):
        children.append(subprocess.Popen([sys.executable,*args],creationflags=flags))
    print('衡尺评测中台: http://127.0.0.1:8765  |  Ctrl+C 停止',flush=True)
    while all(p.poll() is None for p in children): time.sleep(.5)
    raise SystemExit('一个服务启动失败；请检查端口占用或上方错误。')
finally:
    for p in children:
        if p.poll() is None: p.terminate()
    for p in children: p.wait()
