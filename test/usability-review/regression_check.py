#!/usr/bin/env python3
"""UX-001 orchestrator browser regression (Claude). Covers gaps not in root's
independent_check.py: skill scope/status/dedupe/jump, scroll preservation,
touch heights and muted-text contrast in light and dark themes. No mocks.
Run: uv run --offline --no-project --with playwright python test/usability-review/regression_check.py
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent

# WCAG relative-luminance contrast of each visible muted/label text against its effective background
CONTRAST_JS = """root => {
  const rgb = s => (s.match(/[\\d.]+/g) || []).map(Number);
  const lum = ([r, g, b]) => [r, g, b].map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; })
                                 .reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
  const bg = e => { for (; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length >= 3 && (c[3] ?? 1) > 0.5) return c; } return [255, 255, 255]; };
  const sel = '.text-muted, .block-desc, .filter-label, .timestamp-label, [class*="label"], [class*="muted"], [class*="subtle"], [class*="note"]';
  return [...root.querySelectorAll(sel)].filter(e => e.offsetParent && e.textContent.trim()).map(e => {
    const L1 = lum(rgb(getComputedStyle(e).color)), L2 = lum(bg(e));
    return { text: e.textContent.trim().slice(0, 30), px: parseFloat(getComputedStyle(e).fontSize),
             ratio: Math.round(((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05)) * 100) / 100 };
  });
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:8787')
    ap.add_argument('--output', type=Path, default=HERE / 'regression-results.json')
    args = ap.parse_args()
    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        def run(name, fn, width=1440):
            ctx = browser.new_context(viewport={'width': width, 'height': 1000 if width > 390 else 844})
            page = ctx.new_page()
            page.set_default_timeout(10000)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            try:
                page.goto(args.url, wait_until='networkidle')
                page.wait_for_selector('#agent-kpi-container .kpi-tile')
                detail, ok = fn(page), True
            except Exception as e:  # record and continue with the next check
                detail, ok = f'{type(e).__name__}: {e}'[:600], False
            results.append({'check': name, 'width': width, 'status': 'passed' if ok and not errors else 'failed',
                            'detail': detail, 'page_errors': errors[:3]})
            ctx.close()

        def skills(page):
            page.click('#nav-skills')
            page.wait_for_selector('#filter-skill-scope')
            rows = lambda: page.locator('#skills-tbody tr:not(:has(td[colspan]))').count()  # skip empty-state row
            r = {'default_scope': page.input_value('#filter-skill-scope'), 'default': rows()}
            page.select_option('#filter-skill-scope', 'all'); r['all'] = rows()
            page.select_option('#filter-skill-scope', 'common')
            for ag in ('codex', 'claude', 'opencode', 'antigravity', '__repository__'):
                page.select_option('#filter-skill-agent', ag); r[ag] = rows()
            # dedupe: no (agent, name) pair repeats in the common list for claude
            page.select_option('#filter-skill-agent', 'claude')
            names = page.locator('#skills-tbody tr td:first-child').all_inner_texts()
            r['claude_dupes'] = len(names) - len(set(names))
            page.select_option('#filter-skill-agent', 'antigravity')
            page.select_option('#filter-skill-status', 'unknown'); r['agy_unknown'] = rows()
            page.select_option('#filter-skill-status', 'enabled'); r['agy_enabled'] = rows()
            page.select_option('#filter-skill-agent', 'ALL')
            page.select_option('#filter-skill-scope', 'all')
            page.select_option('#filter-skill-status', 'disabled'); r['all_disabled'] = rows()
            page.select_option('#filter-skill-status', 'ALL')
            page.select_option('#filter-skill-scope', 'common')
            r['count_text'] = page.locator('#view-skills [aria-live="polite"]').all_inner_texts()
            r['summary_has_36'] = '36' in page.inner_text('#skills-summary-cards')
            # survives a refresh
            page.select_option('#filter-skill-status', 'enabled')
            before = rows()
            page.click('#btn-manual-refresh'); page.wait_for_timeout(900)
            r['status_kept'] = page.input_value('#filter-skill-status') == 'enabled' and rows() == before
            assert r['default_scope'] == 'common' and r['all'] >= 812 and r['default'] < r['all'], r
            assert r['codex'] == r['claude'] == r['opencode'] == r['antigravity'] == 36, r
            assert r['__repository__'] >= 1 and r['claude_dupes'] == 0, r
            assert r['agy_unknown'] == 36 and r['agy_enabled'] == 0 and r['all_disabled'] >= 600, r
            assert r['count_text'] and r['summary_has_36'] and r['status_kept'], r
            return r
        run('skills scope/status/dedupe', skills)

        def jump(page, width):
            page.click('#nav-skills')
            page.wait_for_selector('#filter-skill-scope')
            out = {}
            for btn, target in (('#btn-jump-mcp', '#title-mcp-section'), ('#btn-jump-list', '#title-skills-list'),
                                ('#btn-jump-overview', '#title-skills-summary')):
                page.click(btn)
                page.wait_for_timeout(1200)
                top = page.locator(target).bounding_box()['y']
                out[target] = {'top': round(top), 'hash': page.evaluate('location.hash'),
                               'focused': page.evaluate('document.activeElement.id')}
                assert -5 <= top < 400 and out[target]['hash'] == '#skills', out
            return out
        for w in (390, 1440):
            run(f'skills jump {w}', lambda p, w=w: jump(p, w), width=w)

        def scroll(page):  # page + table horizontal scroll survive refresh and language change
            # <body> is the scroller (html/body height:100%), so read whichever element actually scrolls
            y = "window.scrollY || document.body.scrollTop"
            page.evaluate('document.body.scrollTop = 900; window.scrollTo(0, 900)')
            page.locator('#model-usage-table').evaluate("t => t.closest('.table-scroll').scrollLeft = 80")
            # programmatic click = same re-render path as the 15s poll; page.click() would first scroll
            # the header button into view and reset the scroller by itself (test artifact)
            page.evaluate("document.getElementById('btn-manual-refresh').click()"); page.wait_for_timeout(900)
            r = {'y_refresh': page.evaluate(y),
                 'x_refresh': page.locator('#model-usage-table').evaluate("t => t.closest('.table-scroll').scrollLeft")}
            page.evaluate("document.getElementById('btn-toggle-lang').click()"); page.wait_for_timeout(600)
            r['y_lang'] = page.evaluate(y)
            assert r['y_refresh'] >= 850 and r['x_refresh'] >= 60 and r['y_lang'] >= 600, r
            return r
        run('scroll preserved', scroll, width=768)

        def theme(page, width):
            out = {}
            for th in ('dark', 'light'):
                if page.get_attribute('html', 'data-theme') != th:
                    page.click('#btn-toggle-theme')
                worst = []
                for v in ('agents', 'hardware', 'skills'):
                    page.click(f'#nav-{v}'); page.wait_for_timeout(300)
                    worst += page.locator('main').evaluate(CONTRAST_JS)
                worst.sort(key=lambda x: x['ratio'])
                out[th] = {'min_ratio': worst[0], 'min_px': min(worst, key=lambda x: x['px']),
                           'below_4_5': [w for w in worst if w['ratio'] < 4.5][:5]}
            if width <= 760:
                page.click('#nav-hardware')
                for sel in ('#btn-manual-refresh', '#btn-toggle-lang', '#btn-toggle-theme', '#nav-agents',
                            '#nav-hardware', '#nav-skills', '.btn-range'):
                    loc = page.locator(sel).first; loc.wait_for(state='visible'); out[sel] = round(loc.bounding_box()['height'])
                page.click('#nav-skills')
                for sel in ('#filter-skill-agent', '#filter-skill-scope', '#filter-skill-status',
                            '#input-skill-search', '#skills-table th button'):
                    loc = page.locator(sel).first; loc.wait_for(state='visible'); out[sel] = round(loc.bounding_box()['height'])
                short = {k: v for k, v in out.items() if isinstance(v, int) and v < 40}
                assert not short, short
            assert not out['dark']['below_4_5'] and not out['light']['below_4_5'], out
            assert out['dark']['min_px']['px'] >= 12 and out['light']['min_px']['px'] >= 12, out
            return out
        for w in (390, 768, 1440):
            run(f'contrast/touch {w}', lambda p, w=w: theme(p, w), width=w)

        def fit(page, width):  # UX-002: body is the scroller, so check body.scrollWidth and header controls
            out = {}
            for th in ('dark', 'light'):
                if page.get_attribute('html', 'data-theme') != th:
                    page.evaluate("document.getElementById('btn-toggle-theme').click()")
                for v in ('agents', 'hardware', 'skills'):
                    page.evaluate(f"document.getElementById('nav-{v}').click()"); page.wait_for_timeout(300)
                    m = page.evaluate("""() => ({body: document.body.scrollWidth, doc: document.documentElement.scrollWidth,
                        vw: innerWidth, clipped: [...document.querySelectorAll('.top-header button, .nav-item')]
                          .filter(e => { const r = e.getBoundingClientRect(); return r.left < 0 || r.right > innerWidth + 1; })
                          .map(e => e.id || e.textContent.trim())})""")
                    out[f'{th}-{v}'] = m
                    assert m['body'] <= m['vw'] + 1 and m['doc'] <= m['vw'] + 1 and not m['clipped'], (th, v, m)
            return {k: v['body'] for k, v in out.items()}
        for w in (390, 768, 1024, 1440):
            run(f'no overflow/clipping {w}', lambda p, w=w: fit(p, w), width=w)

        browser.close()

    out = {'checked_at': datetime.now(timezone.utc).isoformat(), 'url': args.url,
           'result': 'PASS' if all(r['status'] == 'passed' for r in results) else 'FAIL', 'checks': results}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(out['result'])
    for r in results:
        print(r['status'], r['check'], json.dumps(r['detail'], ensure_ascii=False)[:500], r['page_errors'])


if __name__ == '__main__':
    main()
