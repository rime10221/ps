# -*- coding: utf-8 -*-
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

BASE = "http://new.edaily.plasticsurgery.or.kr"
main_handle = driver.current_window_handle

driver.switch_to.new_window("tab")
driver.get(BASE + "/popup/code.php?v=1&sv=0&mode=a")
time.sleep(1.5)

# 검색 트리거 요소 조사 (검색 글자를 가진 요소)
print("[검색 관련 클릭 요소]")
for el in driver.find_elements("css selector", "a, button, input[type=button], input[type=submit], span, img"):
    txt = (el.text or el.get_attribute("value") or el.get_attribute("alt") or "")
    oc = el.get_attribute("onclick")
    if "검색" in txt or (oc and ("search" in oc.lower() or "keyword" in oc.lower())):
        print("  tag=%-7s text=%-10s onclick=%s" % (el.tag_name, txt[:10], oc))

# keyword input 의 이벤트 처리 방식 확인 위해 페이지 스크립트 함수명 grep
print("\n[페이지 내 검색 함수 힌트 - script 안 search 관련]")
html = driver.page_source
import re
for m in re.findall(r"function\s+(\w+)\s*\([^)]*\)", html):
    print("  function", m)

# 실제 검색 수행: 상병명으로 검색
kw = driver.find_element("id", "search_keyword")
kw.clear()
kw.send_keys("Fracture of frontal sinus")
kw.send_keys(Keys.ENTER)
time.sleep(2.5)

print("\n[검색 후 결과 테이블 행]")
rows = driver.find_elements("css selector", "table tr")
for i, r in enumerate(rows[:15]):
    tds = r.find_elements("tag name", "td")
    if not tds:
        continue
    cells = [td.text for td in tds]
    print(f"  row{i}: {cells}")
    # 관리 칸의 버튼/링크 onclick
    for a in r.find_elements("css selector", "a, input[type=button], button"):
        print("       [관리요소] tag=%s text=%s value=%s onclick=%s" % (
            a.tag_name, (a.text or "")[:12], a.get_attribute("value"),
            str(a.get_attribute("onclick"))[:120]))

# 코드로도 검색 테스트
print("\n\n[코드 'S0211' 로 검색]")
kw = driver.find_element("id", "search_keyword")
kw.clear()
kw.send_keys("S0211")
kw.send_keys(Keys.ENTER)
time.sleep(2.5)
rows = driver.find_elements("css selector", "table tr")
for i, r in enumerate(rows[:12]):
    tds = r.find_elements("tag name", "td")
    if not tds:
        continue
    print(f"  row{i}: {[td.text for td in tds]}")
    for a in r.find_elements("css selector", "a, input[type=button], button"):
        print("       [관리] onclick=%s" % str(a.get_attribute("onclick"))[:120])

print("\n(팝업 탭은 열어둡니다 - 구조 재확인용)")
