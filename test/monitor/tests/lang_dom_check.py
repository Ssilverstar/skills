#!/usr/bin/env python3
"""QA-003: FE-008·FE-009 영어 모드 실제 브라우저 DOM 한글 잔존 검사.

실행: cd test/monitor && uv run --with playwright==1.63.0 python tests/lang_dom_check.py
- Chromium headless(기존 ~/.cache/ms-playwright 사용, 설치 없음), viewport 1440x1000·390x844.
- 실제 버튼으로 영어 전환 → #agents/#hardware/#skills 해시 이동 → details 전부 open →
  범위 버튼 ≥1 → 정렬 버튼 ≥1 → innerText·title·aria-label·placeholder·alt·document.title 스캔.
- 한국어 복귀 후 한글 노출 확인, 390px 가로 스크롤 없음, 콘솔 error 0.
- 결과 JSON 한 줄 출력, 실패 시 exit 1. 스크린샷은 test/.local/ignored/qa003/에만.
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUTDIR = Path(__file__).resolve().parents[2] / ".local" / "ignored" / "qa003"
VIEWS = ["agents", "hardware", "skills"]
VIEWPORTS = [(1440, 1000), (390, 844)]
MAX_RECORD = 50

# 화면에 보이는 요소만: title/aria-label/placeholder/alt + body.innerText + document.title.
# (display:none 뷰의 정적 속성 잔존은 AC4 "화면 전체" 위반이 아니므로 별도 note로 분리.)
SCAN_JS = """
() => {
  const re = /[가-힣]/;
  const items = [];
  const hiddenAttrs = [];
  const sel = (el) => {
    if (el.id) return '#' + el.id;
    let cls = '';
    try { if (typeof el.className === 'string' && el.className.trim()) cls = '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.'); } catch (e) {}
    return el.tagName.toLowerCase() + cls;
  };
  const visible = (el) => !!(el.getClientRects && el.getClientRects().length);
  const win = (s) => { const i = s.search(/[가-힣]/); return s.slice(Math.max(0, i - 20), i + 40); };
  const seen = new Set();
  const push = (where, value, selector, bucket) => {
    const s = String(value);
    if (re.test(s)) {
      const key = where + '|' + s.slice(0, 120);
      if (!seen.has(key)) {
        seen.add(key);
        bucket.push({ where, selector, text: s.slice(0, 60), match_window: win(s) });
      }
    }
  };
  push('title', document.title, 'title', items);
  push('body', document.body.innerText, 'body', items);
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let tn;
  while ((tn = tw.nextNode())) {
    const p = tn.parentElement;
    if (tn.textContent && re.test(tn.textContent) && p && visible(p)) push('text', tn.textContent, sel(p), items);
  }
  for (const el of document.querySelectorAll('*')) {
    for (const attr of ['title', 'aria-label', 'placeholder', 'alt']) {
      const v = el.getAttribute ? el.getAttribute(attr) : null;
      if (v) push('attr:' + attr, v, sel(el), visible(el) ? items : hiddenAttrs);
    }
  }
  // 닫힌 select의 option 텍스트는 렌더 여부와 무관하게 영어여야 하므로 항상 검사 대상.
  for (const op of document.querySelectorAll('select option')) {
    if (op.textContent) push('option', op.textContent, sel(op.parentElement || document.createElement('select')) + ' > option[value=' + (op.value || '') + ']', items);
  }
  return { visible: items.slice(0, 50), visible_total: items.length, hidden_attrs: hiddenAttrs.slice(0, 10), hidden_attrs_total: hiddenAttrs.length };
}
"""

REPO_FILTER_JS = """
() => {
  const sel = document.getElementById('filter-skill-agent');
  const opt = sel ? sel.querySelector('option[value="__repository__"]') : null;
  return {
    label: opt ? opt.textContent.trim() : null,
    selected: sel ? sel.value : null,
    rows: document.querySelectorAll('#skills-tbody tr').length
  };
}
"""

MCP_CARDS_JS = """
() => {
  const grid = document.querySelector('#view-skills .mcp-summary-grid');
  if (!grid) return { present: false, count: 0, names: [] };
  const kids = Array.from(grid.children);
  const names = kids.map(k => {
    const n = k.querySelector('.kpi-agent-name');
    return (n ? n.textContent : '').trim().toLowerCase();
  });
  return { present: true, count: kids.length, names };
}
"""

MCP_EXPECT = {"codex", "claude", "opencode", "antigravity"}


def run_viewport(browser, width, height):
    report = {"viewport": f"{width}x{height}", "views": {}, "console_errors": [],
              "screenshots": [], "lang_before_toggle": None, "lang_after_toggle": None,
              "ko_visible_hits": None, "scroll_ok": None, "range_clicked": {},
              "sort_clicked": {}, "mcp_cards": None, "repo_filter": None}
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.on("console", lambda m: report["console_errors"].append(m.text[:80]) if m.type == "error" else None)
    page.on("pageerror", lambda e: report["console_errors"].append(str(e)[:80]))

    page.goto(BASE + "/#agents", wait_until="networkidle")
    page.wait_for_selector("#view-agents", state="visible")
    report["lang_before_toggle"] = page.evaluate("document.documentElement.lang")
    page.click("#btn-toggle-lang")  # 한국어로 로드한 뒤 화면의 실제 버튼으로 영어 전환
    report["lang_after_toggle"] = page.evaluate("document.documentElement.lang")

    for view in VIEWS:
        page.goto(f"{BASE}/#{view}")
        page.wait_for_selector(f"#view-{view}", state="visible")
        page.evaluate("document.querySelectorAll('details').forEach(d => { d.open = true; })")
        rng = page.locator(f"#view-{view} button.btn-range")
        report["range_clicked"][view] = rng.count()
        if rng.count() > 0:
            rng.first.click()
            page.wait_for_timeout(400)
        srt = page.locator(f"#view-{view} .th-sort-btn")
        report["sort_clicked"][view] = srt.count()
        if srt.count() > 0:
            srt.first.click()
            page.wait_for_timeout(300)
        report["views"][view] = page.evaluate(SCAN_JS)
        if view == "skills":
            report["mcp_cards"] = page.evaluate(MCP_CARDS_JS)
            try:
                page.select_option("#filter-skill-agent", "__repository__")
                page.wait_for_timeout(300)
            except Exception as exc:
                report["repo_filter"] = {"error": str(exc)[:80]}
            report["repo_filter"] = report.get("repo_filter") or page.evaluate(REPO_FILTER_JS)
        shot = OUTDIR / f"en_{view}_{width}.png"
        page.screenshot(path=str(shot))
        report["screenshots"].append(str(shot))

    # 한국어 토글 복귀 → 한글이 실제로 보이는지 (토글 동작 확인)
    page.click("#btn-toggle-lang")
    page.wait_for_timeout(300)
    report["ko_visible_hits"] = page.evaluate(
        "() => (document.body.innerText.match(/[가-힣]/g) || []).length")
    page.screenshot(path=str(OUTDIR / f"ko_home_{width}.png"))

    report["scroll_ok"] = page.evaluate(
        "() => document.documentElement.scrollWidth <= window.innerWidth")
    ctx.close()
    return report


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary = {"task": "QA-003", "base": BASE, "pass": False, "reports": [], "error": None}
    failures = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width, height in VIEWPORTS:
                rep = run_viewport(browser, width, height)
                summary["reports"].append(rep)
                if rep["lang_before_toggle"] != "ko" or rep["lang_after_toggle"] != "en":
                    failures.append(f"{rep['viewport']}: lang {rep['lang_before_toggle']}→{rep['lang_after_toggle']}")
                for view, scan in rep["views"].items():
                    if scan["visible_total"] > 0:
                        failures.append(f"{rep['viewport']}/{view}: hangul={scan['visible_total']}")
                mcp = rep.get("mcp_cards") or {}
                names = set(mcp.get("names", []))
                if not mcp.get("present") or mcp.get("count") != 4 or names != MCP_EXPECT or "gemini" in names:
                    failures.append(f"{rep['viewport']}: mcp_cards={mcp}")
                rf = rep.get("repo_filter") or {}
                if rf.get("label") != "Repository Origin" or (rf.get("rows") or 0) < 1 or rf.get("selected") != "__repository__":
                    failures.append(f"{rep['viewport']}: repo_filter={rf}")
                if not rep["console_errors"]:
                    pass
                else:
                    failures.append(f"{rep['viewport']}: console_errors={len(rep['console_errors'])}")
                if not (rep["ko_visible_hits"] or 0) > 0:
                    failures.append(f"{rep['viewport']}: ko_toggle_no_hangul")
                if width == 390 and rep["scroll_ok"] is not True:
                    failures.append("390: horizontal scroll")
            browser.close()
    except Exception as exc:  # 브라우저·서버 접근 실패 등
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        failures.append("runtime_error")

    summary["failures"] = failures
    summary["pass"] = not failures
    summary["hangul_records"] = [
        {"viewport": rep["viewport"], "view": view, **hit}
        for rep in summary["reports"]
        for view, scan in rep["views"].items()
        for hit in scan["visible"][:MAX_RECORD]
    ]
    (OUTDIR / "dom_summary.json").write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
