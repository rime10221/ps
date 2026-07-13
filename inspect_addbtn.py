# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# 메인 탭으로 전환 (regist.php)
for h in driver.window_handles:
    driver.switch_to.window(h)
    if "regist.php" in driver.current_url:
        break
print("현재:", driver.current_url)

print("\n[.add_a_sub 버튼]")
for el in driver.find_elements("css selector", ".add_a_sub"):
    print("  text=%s data(행번호)=%s" % (el.text, el.get_attribute("data")))

print("\n[첫 환자행 admission_1 전체 HTML]")
tr = driver.find_elements("css selector", "#admission_1")
if tr:
    print(tr[0].get_attribute("outerHTML"))
