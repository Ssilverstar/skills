#!/usr/bin/env python3
"""Independent real-browser checks. Optional Playwright 1.63 test dependency."""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8787')
    parser.add_argument('--output', type=Path, default=Path(__file__).parents[1]/'results/monitor-e2e.json')
    parser.add_argument('--screenshots', type=Path, default=Path(__file__).parents[1]/'.local/monitor-screenshots')
    args = parser.parse_args()
    args.screenshots.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='ko-KR')
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        response = page.goto(args.url, wait_until='networkidle')
        assert response.status == 200
        page.wait_for_function("document.querySelectorAll('#agent-tokens-tbody tr').length === 4")
        assert page.locator('nav a').count() == 3
        assert page.locator('#agent-kpi-container .kpi-tile').count() == 4
        assert '미확인' in page.locator('#agent-tokens-tbody').inner_text()
        checks.append('live: three navigation entries, four agents, missing usage remains unknown')
        page.screenshot(path=str(args.screenshots/'agents-desktop.png'))
        page.locator('#nav-hardware').click()
        page.wait_for_selector('#view-hardware:not(.hidden)')
        assert 'NVIDIA GB10' in page.locator('#gpu-details').inner_text()
        inference = page.locator('#inference-details').inner_text()
        assert 'llama.cpp' in inference and 'vllm' in inference.lower()
        assert '미확인' in page.locator('#gpu-details').inner_text() or '미지원' in page.locator('#gpu-details').inner_text()
        page.wait_for_selector('#chart-svg-gpu-util svg')
        checks.append('live: GB10, real runtime/package distinction, unknown VRAM, rendered history charts')
        page.screenshot(path=str(args.screenshots/'hardware-desktop.png'))
        history_rows = page.locator('#snapshot-history-tbody tr')
        assert history_rows.count() > 1
        history_rows.last.scroll_into_view_if_needed()
        rect = history_rows.last.bounding_box()
        assert rect and 0 <= rect['y'] < 1000
        page.screenshot(path=str(args.screenshots/'hardware-history.png'))
        page.locator('#nav-skills').click()
        assert page.locator('#skills-summary-cards .skill-summary-card').count() == 4
        assert page.locator('#mcp-container .kpi-tile').count() == 4
        assert page.locator('#mcp-status-tbody tr').count() >= 12
        mcp_agents = page.locator('#mcp-status-tbody tr td:first-child').all_text_contents()
        assert set(mcp_agents) == {'codex', 'claude', 'opencode', 'antigravity'}, mcp_agents
        checks.append('live: four agent KPI cards, four skill cards and four MCP cards with common server details')
        page.locator('#input-skill-search').fill('ponytail-help')
        assert page.locator('#skills-tbody tr').count() >= 4
        page.locator('#filter-skill-agent').select_option('opencode')
        assert page.locator('#skills-tbody tr').count() == 1
        assert 'ponytail-help' in page.locator('#skills-tbody').inner_text()
        checks.append('live: skill name search and agent filtering')
        page.screenshot(path=str(args.screenshots/'skills-desktop.png'))
        page.locator('#input-skill-search').fill('')
        page.locator('#filter-skill-agent').select_option('ALL')
        for route in ['agents', 'hardware', 'skills']:
            page.set_viewport_size({'width': 390, 'height': 844})
            page.goto(args.url + '/#' + route, wait_until='networkidle')
            assert page.locator('#view-' + route).is_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), route + ' page-level horizontal overflow'
        checks.append('live: three views at 390px without page-level horizontal overflow')
        page.screenshot(path=str(args.screenshots/'skills-mobile.png'))

        # All four language/theme combinations and persisted preferences in a real browser.
        page.set_viewport_size({'width':1440, 'height':1000})
        page.goto(args.url, wait_until='networkidle')
        for lang, theme in [('en','light'), ('en','dark'), ('ko','light'), ('ko','dark')]:
            if page.locator('html').get_attribute('lang') != lang:
                page.locator('#btn-toggle-lang').click()
            if page.locator('html').get_attribute('data-theme') != theme:
                page.locator('#btn-toggle-theme').click()
            assert page.locator('html').get_attribute('lang') == lang
            assert page.locator('html').get_attribute('data-theme') == theme
            page.reload(wait_until='networkidle')
            assert page.locator('html').get_attribute('lang') == lang
            assert page.locator('html').get_attribute('data-theme') == theme
            page.screenshot(path=str(args.screenshots/f'agents-{lang}-{theme}.png'))
        checks.append('live: all four language/theme combinations survive reload')
        if page.locator('html').get_attribute('lang') != 'en':
            page.locator('#btn-toggle-lang').click()
        for view in ('agents','hardware','skills'):
            page.locator('#nav-'+view).click()
            page.locator('details').evaluate_all('(items) => items.forEach(e => e.open = true)')
            texts=[page.title(), page.locator('body').inner_text()]
            texts += page.locator('option').all_text_contents()
            texts += page.locator('[title],[aria-label],[placeholder],[alt]').evaluate_all('''items => items.flatMap(e =>
                ['title','aria-label','placeholder','alt'].map(a => e.getAttribute(a) || ''))''')
            korean=[line for text in texts for line in text.splitlines() if re.search('[가-힣ㄱ-ㅎㅏ-ㅣ]',line)]
            assert not korean, (view, korean[:15])
            page.screenshot(path=str(args.screenshots/f'{view}-english-expanded.png'), full_page=True)
        checks.append('live: English-only text, expanded details, titles and accessibility labels across every view')
        page.locator('#skills-summary-cards').screenshot(path=str(args.screenshots/'skills-dashboard-en.png'))
        page.locator('#mcp-container').screenshot(path=str(args.screenshots/'mcp-dashboard-en.png'))
        repo_filter = page.locator('#filter-skill-agent')
        repo_filter.select_option('__repository__')
        repo_count = page.locator('#skills-tbody tr').count()
        assert repo_count > 0
        page.locator('#btn-toggle-lang').click()
        assert repo_filter.input_value() == '__repository__'
        assert page.locator('#skills-tbody tr').count() == repo_count
        page.locator('#btn-toggle-lang').click()
        assert repo_filter.locator('option:checked').inner_text() == 'Repository Origin'
        repo_filter.select_option('ALL')
        checks.append('live: repository skill filter retains selection and results across language changes')

        for view, table in [('agents','agent-tokens-table'), ('agents','model-usage-table'),
                            ('hardware','snapshot-history-table'), ('skills','skills-table'),
                            ('skills','skills-category-table'), ('skills','mcp-status-table')]:
            page.locator('#nav-'+view).click()
            page.wait_for_selector('#'+table+' th button')
            count = page.locator('#'+table+' th button').count()
            for index in range(count):
                header = page.locator('#'+table+' th').nth(index)
                header.locator('button').click()
                first = header.get_attribute('aria-sort')
                assert first in ('ascending', 'descending'), (table,index,first)
                header.locator('button').focus()
                page.keyboard.press('Enter')
                assert header.get_attribute('aria-sort') != first, (table,index,'keyboard')
            page.locator('#btn-toggle-lang').click()
            assert page.locator('#'+table+' th').last.get_attribute('aria-sort') in ('ascending','descending')
        checks.append('live: every column of all six tables sorts both ways, keyboard and language changes preserve sorting')

        # Synthetic client-only interception: never alter the production snapshot.
        state = context.request.get(args.url + '/api/snapshot').json()
        assert state['snapshot']
        fixture = json.loads(json.dumps(state))
        for agent, value in zip(fixture['snapshot']['agents'], [2, 100, None, 10]):
            agent['usage']['total_tokens'] = value
        page.route('**/api/snapshot', lambda route: route.fulfill(json=fixture))
        page.goto(args.url+'/#agents', wait_until='networkidle')
        page.reload(wait_until='networkidle')  # A hash-only navigation does not refetch.
        total_header = page.locator('#agent-tokens-table th').nth(6)
        total_header.locator('button').click()  # numeric defaults descending
        names = [a['name'] for a in fixture['snapshot']['agents']]
        def ordered_names():
            return page.locator('#agent-tokens-tbody tr td:first-child').all_text_contents()
        assert ordered_names() == [names[1], names[3], names[0], names[2]], ordered_names()
        total_header.locator('button').click()
        assert ordered_names() == [names[0], names[3], names[1], names[2]], ordered_names()
        page.locator('#btn-manual-refresh').click()
        page.wait_for_timeout(300)
        assert ordered_names() == [names[0], names[3], names[1], names[2]]
        checks.append('fixture: numeric 2/10/100 ordering, unknown last in both directions, sort retained after refresh')
        page.unroute('**/api/snapshot')
        fixture['status'] = 'stale'; fixture['age_seconds'] = 10000
        fixture['snapshot']['agents'][0]['name'] = '<img src=x onerror="window.__xss=1">'
        page.route('**/api/snapshot', lambda route: route.fulfill(json=fixture))
        page.goto(args.url, wait_until='networkidle')
        assert page.locator('#stale-banner').is_visible()
        assert page.evaluate('window.__xss === undefined')
        assert '<img src=x' in page.locator('#agent-cards-container').inner_text()
        checks.append('fixture: stale warning and literal rendering of HTML-like agent name')
        page.unroute('**/api/snapshot')
        page.route('**/api/snapshot', lambda route: route.fulfill(json={'status':'waiting', 'snapshot':None}))
        page.reload(wait_until='networkidle')
        assert page.locator('#view-waiting').is_visible()
        checks.append('fixture: first-snapshot waiting state')
        assert not errors, errors
        context.close(); browser.close()
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'result':'PASS', 'tested_url': args.url,
              'execution_location': 'Browser on DGX host; not a remote Windows client', 'checks':checks, 'browser_errors':errors,
              'fixtures':'Client-side route interceptions only; no production data modified'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
