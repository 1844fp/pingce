from pathlib import Path
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1050})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765');page.wait_for_load_state('networkidle')
    page.get_by_label('评测范围',exact=True).select_option('knowledge')
    page.get_by_role('button',name='准备写作评测',exact=True).click()
    expect(page.get_by_text('用例已发布，目标源码哈希已冻结。重复准备会创建独立新版本。')).to_be_visible(timeout=15000)
    page.get_by_role('button',name='运行真实模块基线',exact=True).click()
    expect(page.get_by_text('待复核 3 · 失败 0',exact=True)).to_be_visible(timeout=30000)
    with page.expect_download() as download:page.get_by_role('button',name='导出证据报告',exact=True).click()
    download.value.save_as(str(root/'reports/local-final-report.json'))
    audit=page.request.get('http://127.0.0.1:8765/api/v1/audit').json()
    assert audit['chain_valid']
    assert any(e['action']=='report.archived' for e in audit['events'])
    page.get_by_role('button',name='操作记录',exact=False).click()
    expect(page.get_by_text('report.archived',exact=True).first).to_be_visible()
    page.screenshot(path=str(root/'docs/local-audit.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors,errors
    browser.close()
    print('PASS local completion: evaluation, immutable archive download, operation chain, mobile')
