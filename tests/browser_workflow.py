from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path.cwd()
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':1440,'height':1000})
 page.goto('http://127.0.0.1:8765');page.wait_for_load_state('networkidle')
 page.get_by_label('评测范围',exact=True).select_option('workflow')
 page.get_by_role('button',name='准备写作评测',exact=True).click()
 expect(page.get_by_text('用例已发布，目标源码哈希已冻结。重复准备会创建独立新版本。')).to_be_visible(timeout=15000)
 page.get_by_role('button',name='运行真实模块基线',exact=True).click()
 expect(page.get_by_text('待复核 4 · 失败 0',exact=True)).to_be_visible(timeout=30000)
 page.screenshot(path=str(root/'docs/workflow-live.png'),full_page=True)
 b.close()
print('workflow live acceptance PASS')
