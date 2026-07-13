# -*- coding: utf-8 -*-
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

BASE = "http://new.edaily.plasticsurgery.or.kr"
main_handle = driver.current_window_handle

def dump(url, label):
    print("\n" + "#" * 75)
    print("#", label, url)
    print("#" * 75)
    driver.switch_to.new_window("tab")
    driver.get(url)
    time.sleep(2)
    print("TITLE:", driver.title)
    print("URL  :", driver.current_url)

    forms = driver.find_elements("tag name", "form")
    print(f"\n[FORM] {len(forms)}")
    for fm in forms:
        print("  name=%s action=%s method=%s" % (fm.get_attribute("name"), fm.get_attribute("action"), fm.get_attribute("method")))

    inputs = driver.find_elements("tag name", "input")
    print(f"\n[INPUT] {len(inputs)}")
    for el in inputs:
        print("  type=%-9s name=%-22s id=%-18s value=%s onclick=%s" % (
            el.get_attribute("type"), el.get_attribute("name"), el.get_attribute("id"),
            str(el.get_attribute("value"))[:20], str(el.get_attribute("onclick"))[:60]))

    for tag in ["select", "textarea", "button"]:
        els = driver.find_elements("tag name", tag)
        print(f"\n[{tag.upper()}] {len(els)}")
        for el in els:
            print("  name=%-22s id=%-18s onclick=%s text=%s" % (
                el.get_attribute("name"), el.get_attribute("id"),
                str(el.get_attribute("onclick"))[:50], (el.text or "")[:30]))

    links = driver.find_elements("css selector", "a[onclick]")
    print(f"\n[A[onclick]] {len(links)}")
    for el in links[:25]:
        print("  text=%-15s onclick=%s" % ((el.text or "")[:15], str(el.get_attribute("onclick"))[:80]))

    # 결과 테이블 헤더 파악
    ths = driver.find_elements("css selector", "th")
    if ths:
        print("\n[TABLE TH]:", [t.text for t in ths][:20])

    # 전체 body 텍스트 앞부분
    print("\n[BODY 텍스트 앞 500자]:")
    print(driver.find_element("tag name", "body").text[:500])

    # 저장 후 창 닫기
    driver.close()
    driver.switch_to.window(main_handle)

dump(BASE + "/popup/code.php?v=1&sv=0&mode=a", "코드조회 팝업")
