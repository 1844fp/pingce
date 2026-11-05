"""Isolated scoped-token browser acceptance; no real credentials or production DB."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1]
folder=root/'work'/('access-'+uuid.uuid4().hex);folder.mkdir(parents=True)
env=os.environ.copy();env['EVAL_DB']=str(folder/'isolated.db')
env['EVAL_AUTH_CONFIG']=json.dumps([{'sha256':hashlib.sha256(b'synthetic-browser-token').hexdigest(),'projects':['allowed'],'access':'read'}])
flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
process=subprocess.Popen([sys.executable,'-m','uvicorn','apps.api.main:app','--host','127.0.0.1','--port','8766'],cwd=root,env=env,creationflags=flags,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            urllib.request.urlopen('http://127.0.0.1:8766/api/v1/health',timeout=1).close();break
        except OSError:time.sleep(.2)
    else:raise RuntimeError('isolated API did not start')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.goto('http://127.0.0.1:8766');page.wait_for_load_state('networkidle')
        expect(page.get_by_role('alert')).to_contain_text('需要服务访问令牌')
        page.get_by_role('button',name='连接设置',exact=False).click()
        page.get_by_label('项目',exact=True).fill('allowed')
        page.get_by_label('服务访问令牌',exact=True).fill('synthetic-browser-token')
        page.get_by_role('button',name='应用连接',exact=True).click()
        page.wait_for_load_state('networkidle')
        expect(page.locator('.workspace')).to_contain_text('allowed')
        page.get_by_role('button',name='准备写作评测',exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('没有所需项目或写入权限')
        page.screenshot(path=str(root/'docs/access-readonly.png'),full_page=True)
        browser.close()
    print('PASS isolated auth browser: missing token, project setting, read allowed, write denied')
finally:
    process.terminate();process.wait(timeout=10)
