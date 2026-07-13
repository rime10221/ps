# -*- coding: utf-8 -*-
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=options)
main = d.current_window_handle

# step=2 를 새 탭에서 열어 추가행 doctor/insurance 확인
d.switch_to.new_window("tab")
d.get("http://new.edaily.plasticsurgery.or.kr/edaily_new/regist.php?step=2&sid=176059")
time.sleep(2)

# in_cnt=1 로 행 확보 (기본 1행 있음)
# 첫 sub행 doctor 옵션
d0 = d.find_element(By.CSS_SELECTOR, "select[name='a_doctor_1[]']")
print("[sv0 전문의 옵션]", [o.get_attribute("value") for o in d0.find_elements(By.TAG_NAME,"option")])

# 추가 버튼 클릭 -> sv1 생성
add = d.find_element(By.CSS_SELECTOR, "a.add_a_sub[data='1']")
d.execute_script("arguments[0].click();", add)
time.sleep(1.2)

docs = d.find_elements(By.CSS_SELECTOR, "select[name='a_doctor_1[]']")
inss = d.find_elements(By.CSS_SELECTOR, "select[name='a_insurance_1[]']")
print("추가 후 a_doctor_1[] 개수:", len(docs), " a_insurance_1[] 개수:", len(inss))
if len(docs) >= 2:
    print("[sv1 전문의 옵션]", [o.get_attribute("value") for o in docs[1].find_elements(By.TAG_NAME,"option")])
if len(inss) >= 2:
    print("[sv1 보험 옵션]", [o.get_attribute("value") for o in inss[1].find_elements(By.TAG_NAME,"option")])

d.close()
d.switch_to.window(main)
print("완료 (임시 탭 닫음)")
