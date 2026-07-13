# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# 버튼 onclick 핸들러
print("[BUTTON onclick]")
for el in driver.find_elements("css selector", "input[type=button]"):
    print("  value=%-18s onclick=%s" % (el.get_attribute("value"), el.get_attribute("onclick")))

# 환자 행(tr) 구조 파악 - 이름 input들의 개수와 위치
print("\n[환자 행 반복 패턴]")
names = driver.find_elements("css selector", "input[name='a_name[]']")
print("  a_name[] 개수(현재 행 수):", len(names))

# _1, _2 ... 접미사로 붙는 select 들
for base in ["surgery_", "a_insurance_", "a_doctor_", "a_consult_", "a_consult_sub_"]:
    els = driver.find_elements("css selector", f"[name^='{base}']")
    print(f"  {base}* : {[e.get_attribute('name') for e in els]}")

# 상단 요약 입력값
print("\n[상단 요약 필드]")
for nm in ["in_cnt", "first_cnt", "re_cnt", "diagnosis_total"]:
    el = driver.find_elements("css selector", f"[name='{nm}']")
    if el:
        print(f"  {nm} = {el[0].get_attribute('value')}")

# 첫 환자 행 전체 HTML (구조 이해용)
print("\n[첫 환자 행 근처 HTML 일부]")
row = driver.find_elements("css selector", "input[name='a_name[]']")
if row:
    tr = row[0].find_element("xpath", "./ancestor::tr[1]")
    print(tr.get_attribute("outerHTML")[:2500])
