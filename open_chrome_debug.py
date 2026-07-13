import subprocess
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9222
USER_DATA_DIR = r"C:\chrome_debug_profile"

# 1) 디버깅 포트를 열어 크롬 실행
subprocess.Popen([
    CHROME_PATH,
    f"--remote-debugging-port={DEBUG_PORT}",
    f"--user-data-dir={USER_DATA_DIR}",
])

# 크롬이 뜰 때까지 잠시 대기
time.sleep(3)

# 2) 셀레니움으로 이미 떠 있는 크롬에 붙기
options = Options()
options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")

driver = webdriver.Chrome(options=options)
driver.get("https://www.google.com")

print("현재 페이지 제목:", driver.title)
print(f"디버깅 포트 {DEBUG_PORT}로 크롬이 실행되었습니다. 창은 계속 열려 있습니다.")

# driver.quit()  # 창을 닫고 싶으면 주석 해제
