import json
import threading
import gzip
import pytest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from apps.api.worker import execute, score


def test_real_http_adapter(monkeypatch):
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200); self.end_headers()
            self.wfile.write(b'{"output":42,"actions":["read_data"]}')
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    monkeypatch.setenv('EVAL_ALLOWED_HOSTS','127.0.0.1')
    try:
        case={'id':'http-case','input':'question','expected':42,'forbidden_actions':['write']}
        spec={'target':{'adapter':'http','url':f'http://127.0.0.1:{server.server_port}/execute'},'dataset':{'snapshot':'fixed'},'timeout_seconds':1}
        output=execute(case,spec)
        assert all(s['status']=='PASS' for s in score(case,output))
        assert requests==[{'input':'question','context':{'snapshot':'fixed','case_id':'http-case'}}]
        assert 'expected' not in requests[0]
        assert score(case,{'output':42,'actions':['write']})[1]['status']=='FAIL'
    finally:
        server.shutdown(); server.server_close(); thread.join()


def test_http_decoded_size_limit_and_no_retry(monkeypatch):
    calls=[]
    compressed=gzip.compress(b'x'*2_000_001)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(1)
            self.send_response(200)
            self.send_header('Content-Encoding','gzip')
            self.send_header('Content-Length',str(len(compressed)))
            self.end_headers();self.wfile.write(compressed)
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('EVAL_ALLOWED_HOSTS','127.0.0.1')
    try:
        with pytest.raises(ValueError,match='2MB'):
            execute({'id':'size','input':'synthetic'},{'target':{'adapter':'http','url':f'http://127.0.0.1:{server.server_port}/'},'dataset':{'snapshot':'fixed'},'timeout_seconds':2})
        assert len(calls)==1
    finally:server.shutdown();server.server_close();thread.join()
