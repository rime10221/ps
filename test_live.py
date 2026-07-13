# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import edaily_core as core

driver = core.attach_chrome(9222)

# 1) xls 파싱 + 기본정보 입력
patients = core.parse_admission_xls(r"C:\Users\Administrator\Desktop\ps\입원목록.xls")
print(f"환자 {len(patients)}명 파싱됨")
core.fill_basic_info(driver, patients)

# 2) 진단명 파싱 + 1행에 입력
with open(r"C:\Users\Administrator\Desktop\ps\진단명.txt", encoding="utf-8") as f:
    dx = core.parse_diagnosis_text(f.read())
print(f"\n진단 {len(dx)}건 파싱됨 → 1행에 입력")
core.fill_diagnosis(driver, 1, dx)

print("\n완료 (저장은 하지 않음). 브라우저에서 확인하세요.")
