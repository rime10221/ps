# -*- coding: utf-8 -*-
import io, sys, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

BASE = "http://new.edaily.plasticsurgery.or.kr"
main_handle = driver.current_window_handle

# ---------- 1) 코드 팝업 JS 소스 확보 ----------
driver.switch_to.new_window("tab")
driver.get(BASE + "/popup/code.php?v=1&sv=0&mode=a")
time.sleep(1.5)
html = driver.page_source

print("=" * 70)
print("코드 팝업: 인라인/외부 스크립트")
print("=" * 70)
# 외부 js 링크
for s in re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html):
    print("  [외부] ", s)

# 인라인 script 블록 전체 출력
scripts = re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", html, re.S)
for i, sc in enumerate(scripts):
    sc = sc.strip()
    if sc:
        print(f"\n--- 인라인 script #{i} ---")
        print(sc[:3000])

driver.close()
driver.switch_to.window(main_handle)

# ---------- 2) 부모(메인) 폼에서 진단 '추가' 관련 요소/함수 ----------
print("\n\n" + "=" * 70)
print("메인 폼: 진단/상병 추가 관련")
print("=" * 70)
main_html = driver.page_source

# a_sick 관련 요소 전부
for el in driver.find_elements("css selector", "[name^='a_sick'], [id^='a_sick']"):
    print("  el tag=%s name=%s id=%s" % (el.tag_name, el.get_attribute("name"), el.get_attribute("id")))

# '추가' 텍스트/이미지 클릭 요소
print("\n[추가/삭제 버튼류]")
for el in driver.find_elements("css selector", "a, input[type=button], img, span, button"):
    txt = (el.text or el.get_attribute("value") or el.get_attribute("alt") or "")
    oc = el.get_attribute("onclick") or ""
    if any(k in txt for k in ["추가", "삭제", "행"]) or any(k in oc for k in ["add", "sick", "row", "Add"]):
        print("  tag=%-7s text=%-12s onclick=%s" % (el.tag_name, txt[:12], oc[:90]))

# 메인 폼 인라인 스크립트에서 함수 정의 목록
print("\n[메인 폼 함수 정의 목록]")
for m in re.findall(r"function\s+(\w+)\s*\(([^)]*)\)", main_html):
    print("  function %s(%s)" % (m[0], m[1]))

# 코드/상병 삽입 관련 함수 본문만 발췌
print("\n[상병/코드 관련 함수 본문]")
for name, body in re.findall(r"function\s+(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}", main_html, re.S):
    if any(k in (name+body).lower() for k in ["sick", "code", "add", "sang", "diag"]):
        print(f"\n--- function {name} ---")
        print(body[:1200])
