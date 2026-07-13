# -*- coding: utf-8 -*-
import io
import sys

# 콘솔 한글 깨짐 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DEBUG_PORT = 9222

options = Options()
options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
driver = webdriver.Chrome(options=options)

print("=" * 70)
print("URL   :", driver.current_url)
print("TITLE :", driver.title)
print("=" * 70)

# ---- iframe 확인 ----
frames = driver.find_elements("tag name", "iframe")
print(f"\n[IFRAME] {len(frames)}개")
for f in frames:
    print("  -", f.get_attribute("name"), f.get_attribute("src"))

# ---- form 확인 ----
forms = driver.find_elements("tag name", "form")
print(f"\n[FORM] {len(forms)}개")
for i, fm in enumerate(forms):
    print(f"  form[{i}] name={fm.get_attribute('name')} action={fm.get_attribute('action')} method={fm.get_attribute('method')}")

# ---- input 요소 ----
inputs = driver.find_elements("tag name", "input")
print(f"\n[INPUT] {len(inputs)}개")
for el in inputs:
    print("  type={:<10} name={:<25} id={:<20} value={}".format(
        str(el.get_attribute("type")),
        str(el.get_attribute("name")),
        str(el.get_attribute("id")),
        str(el.get_attribute("value"))[:30],
    ))

# ---- select 요소 ----
selects = driver.find_elements("tag name", "select")
print(f"\n[SELECT] {len(selects)}개")
for el in selects:
    opts = el.find_elements("tag name", "option")
    opt_txt = [f"{o.get_attribute('value')}:{o.text}" for o in opts]
    print("  name={:<25} id={:<20} options={}".format(
        str(el.get_attribute("name")),
        str(el.get_attribute("id")),
        opt_txt,
    ))

# ---- textarea 요소 ----
areas = driver.find_elements("tag name", "textarea")
print(f"\n[TEXTAREA] {len(areas)}개")
for el in areas:
    print("  name={:<25} id={}".format(
        str(el.get_attribute("name")), str(el.get_attribute("id"))))

# ---- 버튼 / submit ----
btns = driver.find_elements("css selector", "button, input[type=submit], input[type=button], a.btn")
print(f"\n[BUTTON/SUBMIT] {len(btns)}개")
for el in btns:
    print("  tag={:<8} type={:<8} name={:<20} text/value={}".format(
        el.tag_name,
        str(el.get_attribute("type")),
        str(el.get_attribute("name")),
        (el.text or el.get_attribute("value") or "")[:30],
    ))
