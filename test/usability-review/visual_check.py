#!/usr/bin/env python3
"""Capture private screenshots and record responsive/contrast measurements."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://192.168.0.65:8787')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent/'visual-results.json')
    parser.add_argument('--shots', type=Path, default=Path(__file__).parents[1]/'.local/usability-review/final')
    args = parser.parse_args()
    args.shots.mkdir(parents=True, exist_ok=True)
    measurements, errors, assets = [], [], {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until='networkidle')
        page.wait_for_selector('#agent-kpi-container .kpi-tile')
        static = Path(__file__).parents[1]/'monitor/app/static'
        for name in ('app.js', 'style.css', 'index.html'):
            route = '/' if name == 'index.html' else '/static/'+name
            response = page.request.get(args.url.rstrip('/')+route)
            local_hash = hashlib.sha256((static/name).read_bytes()).hexdigest()
            served_hash = hashlib.sha256(response.body()).hexdigest()
            assets[name] = {'source_sha256': local_hash, 'served_sha256': served_hash,
                            'matches': response.status == 200 and local_hash == served_hash}
        if page.locator('html').get_attribute('lang') != 'en':
            page.locator('#btn-toggle-lang').click()
        for theme in ('dark', 'light'):
            if page.locator('html').get_attribute('data-theme') != theme:
                page.locator('#btn-toggle-theme').click()
            for width in (1440, 768, 390):
                page.set_viewport_size({'width': width, 'height': 1000 if width > 390 else 844})
                for view in ('agents', 'hardware', 'skills'):
                    page.locator('#nav-'+view).click()
                    page.wait_for_selector('#view-'+view+':not(.hidden)')
                    page.evaluate("window.scrollTo(0,0);document.body.scrollTop=0;document.querySelector('main').scrollTop=0")
                    page.screenshot(path=str(args.shots/f'{view}-{width}-{theme}.png'))
                    measured = page.locator('#view-'+view).evaluate('''root => {
                      const rgb = value => (value.match(/[\\d.]+/g)||[]).map(Number);
                      const luminance = c => c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
                      const contrast = el => {
                        const fg=rgb(getComputedStyle(el).color);
                        let bg, current=el;
                        while(current){
                          const c=rgb(getComputedStyle(current).backgroundColor);
                          if(c.length===3 || c[3]===1){bg=c;break;}
                          current=current.parentElement;
                        }
                        if(!bg || (fg.length===4 && fg[3]!==1)) return null;
                        const a=luminance(fg), b=luminance(bg);
                        return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
                      };
                      const labels=[...root.querySelectorAll('.kpi-metric-label,.block-desc,.filter-label,.text-muted')].filter(e=>e.getClientRects().length);
                      return {
                        page_overflow:document.documentElement.scrollWidth>innerWidth,
                        body_overflow:document.body.scrollWidth>innerWidth,
                        navigation:[...document.querySelectorAll('nav a')].map(e=>{const r=e.getBoundingClientRect();return {x:r.x,right:r.right,height:r.height}}),
                        header_controls:[...document.querySelectorAll('#btn-manual-refresh,#btn-toggle-lang,#btn-toggle-theme')].map(e=>{const r=e.getBoundingClientRect();return {x:r.x,right:r.right,height:r.height}}),
                        muted_labels:labels.map(e=>({selector:e.className,font_px:parseFloat(getComputedStyle(e).fontSize),contrast:contrast(e)})),
                        skill_rows:root.querySelectorAll('#skills-tbody tr').length
                      };
                    }''')
                    labels = {}
                    for label in measured['muted_labels']:
                        key = json.dumps(label, sort_keys=True)
                        labels.setdefault(key, {**label, 'count': 0})['count'] += 1
                    measured['muted_labels'] = list(labels.values())
                    measurements.append({'view':view,'width':width,'theme':theme,**measured})
        browser.close()
    failures=[]
    for m in measurements:
        key=f"{m['view']}/{m['width']}/{m['theme']}"
        if m['page_overflow'] or m['body_overflow'] or any(n['x'] < -1 or n['right'] > m['width']+1 for n in m['navigation']):
            failures.append(key+': overflow/navigation clipping')
        if any(n['x'] < -1 or n['right'] > m['width']+1 for n in m['header_controls']):
            failures.append(key+': clipped header controls')
        for label in m['muted_labels']:
            if label['font_px'] < 12 or (label['contrast'] is not None and label['contrast'] < 4.5):
                failures.append(key+': '+str(label))
    if not all(a['matches'] for a in assets.values()):
        failures.append('Deployed assets differ from local source')
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'url':args.url,
            'result':'PASS' if not failures and not errors else 'FAIL',
            'scope':'18 viewport/theme captures; sampled opaque muted text contrast only, not a full accessibility audit',
            'failures':failures,'page_errors':errors,'assets':assets,'measurements':measurements}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'captures':len(measurements),
                      'failures':len(failures),'page_errors':errors},ensure_ascii=False))
    return 0 if result['result']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
