"""Live browser acceptance; creates synthetic writing runs, never approves real manuscripts."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765'); page.wait_for_load_state('networkidle')
    expect(page.get_by_role('heading',name='AI 写作助手质量闭环')).to_be_visible()
    page.get_by_role('button',name='准备写作评测',exact=True).click()
    expect(page.get_by_text('用例已发布，目标源码哈希已冻结。重复准备会创建独立新版本。')).to_be_visible(timeout=15000)
    page.get_by_role('button',name='运行真实模块基线',exact=True).click()
    expect(page.get_by_text('待复核 8 · 失败 0',exact=True)).to_be_visible(timeout=20000)
    page.screenshot(path=str(root/'docs/writing-baseline.png'),full_page=True)
    # Exercise one review with a rejection; never silently approve subjective quality.
    page.locator('details').filter(has=page.locator('summary',has_text='real-normal')).locator('summary').click()
    page.get_by_label('复核依据 real-normal',exact=True).fill('合成验收：仅验证复核流程，缺少真实原文故暂不通过')
    page.get_by_role('button',name='复核不通过',exact=True).click()
    expect(page.get_by_text('待复核 7 · 失败 1',exact=True)).to_be_visible(timeout=10000)
    with page.expect_download() as download:
        page.get_by_role('button',name='导出证据报告',exact=True).click()
    download.value.save_as(str(root/'docs/writing-browser-baseline-report.json'))
    page.get_by_role('button',name='注入回归并验证',exact=True).click()
    expect(page.get_by_text('待复核 1 · 失败 7',exact=True)).to_be_visible(timeout=20000)
    page.get_by_role('button',name='与最近基线逐样本比较',exact=True).click()
    expect(page.get_by_role('heading',name='新增失败 7 项 · 失败已消除 0 项')).to_be_visible()
    page.get_by_role('button',name='失败样本转回归集',exact=True).click()
    expect(page.get_by_text('已生成「写作模块 · 回归注入验证 · 失败回归集」，可在实验工作台重新运行。')).to_be_visible()
    page.screenshot(path=str(root/'docs/writing-regression.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(root/'docs/writing-mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
    print('PASS: actual module baseline, review, report download, 7 injected failures, comparison, regression dataset, mobile')
