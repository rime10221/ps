# -*- coding: utf-8 -*-
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=options)

print("=== 열린 탭 ===")
er_handle = None
for h in d.window_handles:
    d.switch_to.window(h)
    print(" -", d.current_url)

# step=03 탭 찾기
for h in d.window_handles:
    d.switch_to.window(h)
    u = d.current_url
    if "step=3" in u or "step=03" in u:
        er_handle = h
        break
if not er_handle:
    # regist.php 중 03일 수도 -> body 텍스트로 EMERGENCY ROOM 확인
    for h in d.window_handles:
        d.switch_to.window(h)
        if "EMERGENCY ROOM" in d.find_element(By.TAG_NAME, "body").text:
            er_handle = h
            break

if not er_handle:
    print("\n!! EMERGENCY ROOM(03) 페이지를 찾지 못함")
    sys.exit()

d.switch_to.window(er_handle)
print("\n=== 03 페이지:", d.current_url, "===")

# emergency 카운트 select
em = d.find_elements(By.ID, "emergency")
print("\n[#emergency select 존재?]", bool(em))
if em:
    opts = em[0].find_elements(By.TAG_NAME, "option")
    print("  옵션수:", len(opts), " 처음:", [o.get_attribute("value") for o in opts[:5]])

# emergency_box / 기존 행
box = d.find_elements(By.ID, "emergency_box")
print("[#emergency_box 존재?]", bool(box))
rows = d.find_elements(By.CSS_SELECTOR, ".emergency_tr")
print("[.emergency_tr 현재 행수]", len(rows))

# EMERGENCY ROOM 섹션 헤더/라벨 확인
print("\n[페이지 내 'EMERGENCY' 텍스트 주변 요소]")
for el in d.find_elements(By.XPATH, "//*[contains(text(),'EMERGENCY ROOM')]"):
    print("  ", el.tag_name, ":", el.text[:60])

# 행이 없으면 1개 만들어서 구조 확인
if em and len(rows) == 0:
    print("\n[emergency 1개 생성해서 구조 확인]")
    d.execute_script("arguments[0].value='1'; arguments[0].dispatchEvent(new Event('change'));", em[0])
    time.sleep(1.5)
    rows = d.find_elements(By.CSS_SELECTOR, ".emergency_tr")
    print("  생성 후 행수:", len(rows))

if rows:
    print("\n[emergency_1 행 HTML]")
    r1 = d.find_elements(By.ID, "emergency_1")
    if r1:
        print(r1[0].get_attribute("outerHTML")[:3000])
