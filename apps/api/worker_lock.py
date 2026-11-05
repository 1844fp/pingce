"""OS-held single worker guard; crash releases lock, file intentionally stays."""
from contextlib import contextmanager
from pathlib import Path
import os


@contextmanager
def exclusive_worker(database):
    path=Path(str(database)+'.worker.lock')
    handle=open(path,'a+b')
    try:
        handle.seek(0,2)
        if handle.tell()==0: handle.write(b'0'); handle.flush()
        handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('此数据库已有 Worker；拒绝重复启动及恢复操作') from exc
        try: yield
        finally:
            handle.seek(0)
            if os.name=='nt': msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(handle,fcntl.LOCK_UN)
    finally: handle.close()
