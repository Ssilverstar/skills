#!/usr/bin/env python3
"""Root-owned usability regressions against the live app; mocks stay in the browser."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://192.168.0.65:8787')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent/'independent-results.json')
    args = parser.parse_args()
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        def check(name, action, width=1440):
            context = browser.new_context(viewport={'width':width, 'height':1000 if width>390 else 844})
            page = context.new_page()
            page.set_default_timeout(10000)
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            try:
                page.goto(args.url, wait_until='networkidle')
                page.wait_for_selector('#agent-kpi-container .kpi-tile')
                page.locator('#btn-toggle-lang').click()
                action(page, context)
                assert not errors, errors
                results.append({'name':name,'result':'PASS'})
            except Exception as error:
                results.append({'name':name,'result':'FAIL','reason':str(error)[:700]})
            finally:
                context.close()

        def details(page, context):
            item=page.locator('#agent-cards-container details').first
            item.locator('summary').click()
            assert item.get_attribute('open') is not None
            with page.expect_response('**/api/snapshot'):
                page.locator('#btn-manual-refresh').click()
            page.wait_for_timeout(300)
            assert item.get_attribute('open') is not None, 'refresh closed expanded details'
            page.locator('#btn-toggle-lang').click()
            assert item.get_attribute('open') is not None, 'language change closed expanded details'
        check('details stay open after refresh and language change',details)

        def focus(page,context):
            page.locator('#nav-skills').click()
            page.wait_for_selector('#view-skills:not(.hidden)')
            button=page.locator('#skills-table th button').first
            button.scroll_into_view_if_needed()
            button.click()
            assert page.evaluate("document.activeElement.closest('table')?.id === 'skills-table'"), 'sorting lost focus'
            with page.expect_response('**/api/snapshot',timeout=22000):
                page.wait_for_timeout(16000)
            assert page.evaluate("document.activeElement.closest('table')?.id === 'skills-table'"), 'polling lost focus'
        check('sort click and automatic polling retain keyboard focus',focus)

        def disconnect(page,context):
            page.route('**/api/snapshot',lambda route:route.abort())
            page.locator('#btn-manual-refresh').click()
            page.wait_for_timeout(700)
            status=page.locator('#status-badge').inner_text().lower()
            assert 'healthy' not in status and re.search('disconnect|offline|error|fail|lost',status), status
            assert page.locator('#agent-kpi-container .kpi-tile').count()==4, 'last successful data lost'
            page.unroute('**/api/snapshot')
            with page.expect_response('**/api/snapshot'):
                page.locator('#btn-manual-refresh').click()
            page.wait_for_timeout(300)
            assert page.locator('#error-banner').is_hidden(), 'recovered connection still shows error'
        check('connection failure is visible, retains data and recovers',disconnect)

        def expiry(page,context):
            fixture=context.request.get(args.url+'/api/snapshot').json()
            agent=fixture['snapshot']['agents'][0]
            agent['plan']['limits']=[
                {'label':'QA expired limit','used_percent':99,'reset_at':'2000-01-01T00:00:00Z'},
                {'label':'QA current limit','used_percent':12,'reset_at':'2099-01-01T00:00:00Z'}]
            page.route('**/api/snapshot',lambda route:route.fulfill(json=fixture))
            with page.expect_response('**/api/snapshot'):
                page.locator('#btn-manual-refresh').click()
            page.wait_for_timeout(300)
            text=page.locator('#agent-kpi-container .kpi-tile').first.inner_text()
            assert 'QA current limit' in text and 'QA expired limit' not in text, text
            card=page.locator('#agent-cards-container').inner_text().lower()
            assert re.search('expired|awaiting|reset passed|refresh pending',card), 'expired quota not identified'
        check('expired quota is excluded from current KPI and marked awaiting refresh',expiry)

        def charts(page,context):
            page.locator('#nav-hardware').click()
            page.wait_for_selector('#chart-svg-gpu-util svg')
            svg=page.locator('#chart-svg-gpu-util svg')
            assert svg.get_attribute('role')=='img'
            assert svg.get_attribute('aria-label') or svg.get_attribute('aria-labelledby')
            assert svg.locator('title').count()>0
            assert page.locator('#view-hardware .btn-range[aria-pressed="true"]').count()==1
        check('charts expose accessible summaries and selected range',charts)

        def mobile(page,context):
            for name in ('agents','hardware','skills'):
                page.locator('#nav-'+name).click()
                rects=page.locator('nav a').evaluate_all('items=>items.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,right:r.right,height:r.height}})')
                assert all(r['x']>=0 and r['right']<=390 for r in rects),rects
                assert all(r['height']>=40 for r in rects),rects
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            heights=page.locator('#btn-manual-refresh,#btn-toggle-lang,#btn-toggle-theme').evaluate_all('items=>items.map(e=>e.getBoundingClientRect().height)')
            assert min(heights)>=40,heights
        check('390px navigation is fully reachable and controls have usable targets',mobile,390)

        def english(page,context):
            for name in ('agents','hardware','skills'):
                page.locator('#nav-'+name).click()
                page.locator('details').evaluate_all('items=>items.forEach(e=>e.open=true)')
                texts=[page.title(),page.locator('body').inner_text(),*page.locator('option').all_text_contents()]
                texts+=page.locator('[title],[aria-label],[placeholder],[alt]').evaluate_all("items=>items.flatMap(e=>['title','aria-label','placeholder','alt'].map(k=>e.getAttribute(k)||''))")
                bad=[line for text in texts for line in text.splitlines() if re.search('[가-힣ㄱ-ㅎㅏ-ㅣ]',line)]
                assert not bad,(name,bad[:6])
        check('English stays English across all views and hidden labels',english)
        browser.close()
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'url':args.url,
            'result':'PASS' if all(c['result']=='PASS' for c in results) else 'FAIL','checks':results,
            'scope':'Independent browser checks; failures and expired quotas are client-only fixtures.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['result']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
