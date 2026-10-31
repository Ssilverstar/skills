const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

describe('FE-001 AC7 Security & XSS Prevention Tests', () => {

  test('AC7: app.js 소스코드 내 innerHTML 사용 금지 검증', () => {
    const appJsPath = path.resolve(__dirname, '../../app/static/app.js');
    const appJsContent = fs.readFileSync(appJsPath, 'utf8');

    // innerHTML 사용이 없어야 함
    const hasInnerHTML = /\.innerHTML\b/.test(appJsContent);
    assert.equal(hasInnerHTML, false, 'app.js는 모든 동적 DOM 삽입에 textContent/createTextNode를 사용해야 하며 innerHTML을 사용해서는 안 됩니다.');
  });

  test('AC7: index.html 내 인라인 스크립트 및 인라인 스타일 금지 검증 (CSP 준수)', () => {
    const indexPath = path.resolve(__dirname, '../../app/static/index.html');
    const indexContent = fs.readFileSync(indexPath, 'utf8');

    // <script> 내부에 코드가 있는지 검사 (src 속성만 허용)
    const inlineScriptMatch = /<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/gi.test(indexContent);
    assert.equal(inlineScriptMatch, false, 'index.html에 인라인 <script> 태그가 없어야 합니다.');

    // <style> 태그 금지
    const hasStyleTag = /<style[\s>]/i.test(indexContent);
    assert.equal(hasStyleTag, false, 'index.html에 <style> 태그가 없어야 합니다.');

    // style="..." 속성 금지
    const hasStyleAttr = /\sstyle=["'][^"']*["']/i.test(indexContent);
    assert.equal(hasStyleAttr, false, 'index.html에 style="..." 속성이 없어야 합니다.');
  });

  test('AC7: 악성 스크립트 페이로드 이스케이프 검증', () => {
    const xssPayload = '<img src=x onerror=alert(1)>';
    const helpers = require('../../app/static/app.js');

    // formatValue는 문자열을 그대로 반환하되 변환/실행하지 않음
    const formatted = helpers.formatValue(xssPayload);
    assert.equal(formatted, xssPayload);
  });

  test('FE-002: 추론 서버 고정 라벨 정의 검증', () => {
    const appJsPath = path.resolve(__dirname, '../../app/static/app.js');
    const appJsContent = fs.readFileSync(appJsPath, 'utf8');

    assert.ok(appJsContent.includes("'실행 런타임'"), "라벨 '실행 런타임'이 포함되어야 함");
    assert.ok(appJsContent.includes("'런타임 버전'"), "라벨 '런타임 버전'이 포함되어야 함");
    assert.ok(appJsContent.includes("'실행 파일'"), "라벨 '실행 파일'이 포함되어야 함");
    assert.ok(appJsContent.includes("'컨테이너 이미지'"), "라벨 '컨테이너 이미지'가 포함되어야 함");
    assert.ok(appJsContent.includes("'이미지 내 vLLM 패키지(미실행)'"), "라벨 '이미지 내 vLLM 패키지(미실행)'이 포함되어야 함");
  });

});
