# -*- coding: utf-8 -*-
"""
E-daily 입원(step=2) 자동화 핵심 로직
- 입원목록.xls 파싱
- 진단명 텍스트 파싱
- 디버깅 크롬(9222) attach 후 폼 입력 / 진단코드 입력
"""
import os
import re
import subprocess
import time

import xlrd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

BASE_URL = "http://new.edaily.plasticsurgery.or.kr/"
DEFAULT_DEBUG_PORT = 9222
DEFAULT_PROFILE = r"C:\chrome_debug_profile"

_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def find_chrome():
    """설치된 chrome.exe 경로 반환 (없으면 None)"""
    for p in _CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def launch_debug_chrome(url=BASE_URL, port=DEFAULT_DEBUG_PORT, profile=DEFAULT_PROFILE):
    """디버깅 포트를 연 크롬 창을 띄우고 url 로 이동.
    이미 같은 프로필/포트로 크롬이 떠 있으면 그 인스턴스에 새 탭으로 열림.
    """
    chrome = find_chrome()
    if not chrome:
        raise FileNotFoundError(
            "chrome.exe 를 찾지 못했습니다. Chrome 설치 경로를 확인하세요.")
    subprocess.Popen([
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        url,
    ])
    return chrome


# ============================================================
# 1. 입력 파싱
# ============================================================
def _clean_cell(v):
    """xlrd 셀값을 문자열로. 숫자 float 는 정수형으로."""
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return str(v)
    return str(v).strip()


def parse_admission_xls(path):
    """입원목록.xls -> 환자 dict 리스트

    반환 각 항목:
      regnum(등록번호), name(성명), sex(M/F), age(str),
      room(병실), doctor(주치의), insurance('1'보험/'2'비보험), raw_ins(원문)
    """
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)

    # 헤더 행 찾기 (등록번호/성명 이 들어있는 행)
    header_row = None
    for r in range(min(sh.nrows, 15)):
        rowvals = [_clean_cell(sh.cell_value(r, c)) for c in range(sh.ncols)]
        if "등록번호" in rowvals and "성명" in rowvals:
            header_row = r
            header = rowvals
            break
    if header_row is None:
        raise ValueError("헤더 행(등록번호/성명)을 찾지 못했습니다.")

    def col(name):
        return header.index(name) if name in header else None

    c_reg = col("등록번호")
    c_name = col("성명")
    c_sa = col("S/A")
    c_room = col("병실")
    c_doctor = col("주치의")
    c_ins = col("보험유형")

    patients = []
    for r in range(header_row + 1, sh.nrows):
        reg = _clean_cell(sh.cell_value(r, c_reg)) if c_reg is not None else ""
        name = _clean_cell(sh.cell_value(r, c_name)) if c_name is not None else ""
        if not reg and not name:
            continue  # 빈 행 스킵

        sa = _clean_cell(sh.cell_value(r, c_sa)) if c_sa is not None else ""
        sex, age = "", ""
        if "/" in sa:
            sex, age = sa.split("/", 1)
            sex, age = sex.strip().upper(), age.strip()

        room = _clean_cell(sh.cell_value(r, c_room)) if c_room is not None else ""
        doctor = _clean_cell(sh.cell_value(r, c_doctor)) if c_doctor is not None else ""
        raw_ins = _clean_cell(sh.cell_value(r, c_ins)) if c_ins is not None else ""
        insurance = "1" if "건강보험" in raw_ins else ("2" if raw_ins else "")

        patients.append({
            "regnum": reg, "name": name, "sex": sex, "age": age,
            "room": room, "doctor": doctor,
            "insurance": insurance, "raw_ins": raw_ins,
        })
    return patients


def parse_diagnosis_text(text):
    """진단명 붙여넣기 텍스트 -> 진단 dict 리스트 (파일 순서 유지)

    각 줄 탭 구분. col[6]=코드(점없음), col[7]=상병명(★=주진단)
    반환: code_raw(S0211), code_nodot(S0211), name_en, is_main
    """
    result = []
    for line in text.splitlines():
        line = line.rstrip("\r\n")
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) < 8:
            continue  # 형식 안 맞는 줄 스킵
        code_raw = cols[6].strip()
        name = cols[7].strip()
        is_main = name.startswith("★")
        name = name.lstrip("★").strip()
        if not name:
            continue
        result.append({
            "code_raw": code_raw,
            "code_nodot": code_raw.replace(".", "").upper(),
            "name_en": name,
            "is_main": is_main,
        })
    return result


def _clean_name(name):
    """이름에서 원문자(ⓣ 등 U+2460~U+24FF) 및 앞뒤 공백 제거"""
    return re.sub(r"[①-⓿]", "", name).strip()


def parse_er_xls(path):
    """ER.xls -> 응급실 환자 dict 리스트

    반환 각 항목: regnum(등록번호), name(성명), sex(M/F), age(str)
    (병실은 항상 ER, 입퇴원여부는 항상 퇴원 → 폼 입력 시 고정)
    """
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)

    header_row = None
    for r in range(min(sh.nrows, 15)):
        rowvals = [_clean_cell(sh.cell_value(r, c)) for c in range(sh.ncols)]
        if "등록번호" in rowvals and "성명" in rowvals:
            header_row = r
            header = rowvals
            break
    if header_row is None:
        raise ValueError("ER.xls 헤더 행(등록번호/성명)을 찾지 못했습니다.")

    def col(name):
        return header.index(name) if name in header else None

    c_reg = col("등록번호")
    c_name = col("성명")
    c_sa = col("S/A")

    patients = []
    for r in range(header_row + 1, sh.nrows):
        reg = _clean_cell(sh.cell_value(r, c_reg)) if c_reg is not None else ""
        name = _clean_name(_clean_cell(sh.cell_value(r, c_name))) if c_name is not None else ""
        if not reg and not name:
            continue
        sa = _clean_cell(sh.cell_value(r, c_sa)) if c_sa is not None else ""
        sex, age = "", ""
        if "/" in sa:
            sex, age = sa.split("/", 1)
            sex, age = sex.strip().upper(), age.strip()
        patients.append({"regnum": reg, "name": name, "sex": sex, "age": age})
    return patients


def _norm(s):
    """비교용 정규화: 소문자 + 다중공백 1개"""
    return re.sub(r"\s+", " ", s).strip().lower()


# ============================================================
# 2. 셀레니움 드라이버
# ============================================================
def attach_chrome(debug_port=9222):
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    return webdriver.Chrome(options=options)


def switch_to_step(driver, step):
    """regist.php?step={step} 탭으로 전환. 없으면 예외.
    step=2: 입원/퇴원(ADMISSION), step=3: OPERATION/EMERGENCY
    """
    for h in driver.window_handles:
        driver.switch_to.window(h)
        url = driver.current_url
        if "regist.php" in url and f"step={step}" in url:
            return driver.current_window_handle
    names = {2: "02 ADMISSION/DISCHARGE", 3: "03 OPERATION/EMERGENCY"}
    raise RuntimeError(
        f"{names.get(step, f'step={step}')} 페이지 탭을 찾지 못했습니다. 해당 페이지를 열어주세요.")


def switch_to_regist(driver):
    """(하위호환) 입원 step=2 탭으로 전환."""
    return switch_to_step(driver, 2)


# ============================================================
# 3. 폼 입력
# ============================================================
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def _set_text(el, value):
    el.clear()
    if value:
        el.send_keys(value)


def fill_basic_info(driver, patients, log=print):
    """입원 명수 설정 후 각 환자행 기본정보 입력"""
    switch_to_step(driver, 2)
    n = len(patients)
    log(f"입원 명수 {n}명 설정...")

    # in_cnt 설정 + change 이벤트 1회 발생 (행 생성/삭제)
    in_cnt = driver.find_element(By.ID, "in_cnt")
    driver.execute_script(
        "arguments[0].value=arguments[1];"
        "arguments[0].dispatchEvent(new Event('change'));",
        in_cnt, str(n))

    # 행 생성 대기
    try:
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".admission_tr")) >= n)
    except TimeoutException:
        cur = len(driver.find_elements(By.CSS_SELECTOR, ".admission_tr"))
        raise RuntimeError(f"환자행 생성 실패 (기대 {n}, 현재 {cur})")

    for idx, p in enumerate(patients, start=1):
        row = driver.find_element(By.ID, f"admission_{idx}")
        log(f"  [{idx}행] {p['regnum']} {p['name']} 입력")

        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='a_regnum[]']"), p["regnum"])
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='a_room[]']"), p["room"])
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='a_name[]']"), p["name"])
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='a_age[]']"), p["age"])

        # 성별
        if p["sex"] == "M":
            driver.find_element(By.ID, f"a_sex_{idx}_1").click()
        elif p["sex"] == "F":
            driver.find_element(By.ID, f"a_sex_{idx}_2").click()

        # 보험 (첫 sub행)
        if p["insurance"]:
            sel = Select(driver.find_element(
                By.CSS_SELECTOR, f"select[name='a_insurance_{idx}[]']"))
            sel.select_by_value(p["insurance"])

        # 전문의 (첫 sub행) — 옵션 텍스트 일치
        if p["doctor"]:
            doc_sel = driver.find_element(
                By.CSS_SELECTOR, f"select[name='a_doctor_{idx}[]']")
            opts = [o.get_attribute("value") for o in doc_sel.find_elements(By.TAG_NAME, "option")]
            if p["doctor"] in opts:
                Select(doc_sel).select_by_value(p["doctor"])
            else:
                log(f"    ! 전문의 '{p['doctor']}' 옵션에 없음 (건너뜀)")

    log("기본정보 입력 완료.")


import difflib
import urllib.parse
import urllib.request

MAKE_CODE_URL = "http://new.edaily.plasticsurgery.or.kr/edaily_new/ajax/make_code.php"
_RESULT_RE = re.compile(r'data="([^"]*)" code="([^"]*)" data_en="([^"]*)"')


def _dot_code(code_raw):
    """무점 코드 -> KCD 점표기 (3번째 글자 뒤에 점). 예: S091 -> S09.1"""
    c = code_raw.upper()
    return c if len(c) <= 3 else c[:3] + "." + c[3:]


def _search_code(keyword):
    """make_code.php 검색 -> [(sid, code, name_en), ...]"""
    if not keyword:
        return []
    data = urllib.parse.urlencode({"keyword": keyword}).encode()
    try:
        with urllib.request.urlopen(MAKE_CODE_URL, data, timeout=10) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception:
        return []
    return _RESULT_RE.findall(html)


def match_diagnosis(dx):
    """진단 dict -> (방법, sid, code, name_en) 또는 None

    1순위: 영문명 정확일치
    2순위: 점표기 코드 검색 결과 중 영문명 유사도 최고
    """
    name = dx["name_en"]
    # 1) 영문명 정확일치
    for sid, code, en in _search_code(name):
        if _norm(en) == _norm(name):
            return ("이름정확", sid, code, en)
    # 2) 점코드 검색 + 유사도
    rows = _search_code(_dot_code(dx["code_raw"]))
    if rows:
        best = max(rows, key=lambda r: difflib.SequenceMatcher(
            None, _norm(r[2]), _norm(name)).ratio())
        return ("코드+유사도", best[0], best[1], best[2])
    return None


# insert_code 와 동일하게 opener(=현재 문서) 필드에 기록
_JS_SET_SICK = """
document.getElementById('a_sick_'+arguments[0]+'_'+arguments[1]).value = arguments[2];
document.getElementById('a_consult_memo_'+arguments[0]+'_'+arguments[1]).value = arguments[3];
document.getElementById('a_sick_sid_'+arguments[0]+'_'+arguments[1]).value = arguments[4];
"""


def _set_select_by_value(sel_el, value):
    """옵션에 값이 있으면 선택. 없으면 무시(False 반환)."""
    opts = [o.get_attribute("value") for o in sel_el.find_elements(By.TAG_NAME, "option")]
    if value in opts:
        Select(sel_el).select_by_value(value)
        return True
    return False


def _set_subrow_ins_doctor(driver, v, sv, insurance, doctor, log):
    """상병 sub행(sv)의 보험/전문의 select 지정 (환자값과 동일하게)"""
    if insurance:
        ins = driver.find_elements(By.CSS_SELECTOR, f"select[name='a_insurance_{v}[]']")
        if sv < len(ins):
            _set_select_by_value(ins[sv], insurance)
    if doctor:
        docs = driver.find_elements(By.CSS_SELECTOR, f"select[name='a_doctor_{v}[]']")
        if sv < len(docs):
            if not _set_select_by_value(docs[sv], doctor):
                log(f"      ! 전문의 '{doctor}' 옵션 없음 (sub {sv})")


def fill_diagnosis(driver, row_index, diagnoses, insurance=None, doctor=None, log=print):
    """선택 환자행(row_index)에 진단코드들 입력.

    사이트의 '코드조회 팝업 > 선택' 이 하는 동작(3개 필드 기록)을 직접 재현.
    2번째 상병부터는 site의 '추가'(add_a_sub) 로 sub행을 만든 뒤 기록.
    각 sub행의 보험/전문의도 환자값(insurance/doctor)과 동일하게 지정.
    """
    switch_to_step(driver, 2)
    v = row_index
    ok = 0

    for i, dx in enumerate(diagnoses):
        sv = i
        mark = "★" if dx["is_main"] else " "

        m = match_diagnosis(dx)

        # 2번째 상병부터 sub행 추가
        if i > 0:
            add_btn = driver.find_element(By.CSS_SELECTOR, f"a.add_a_sub[data='{v}']")
            driver.execute_script("arguments[0].click();", add_btn)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"a_sick_{v}_{sv}")))

        # 보험/전문의 지정 (모든 sub행)
        _set_subrow_ins_doctor(driver, v, sv, insurance, doctor, log)

        if m is None:
            log(f"  [{mark}] {dx['code_raw']} {dx['name_en']}  → ! 매칭 실패")
            continue

        how, sid, code, en = m
        driver.execute_script(_JS_SET_SICK, str(v), str(sv), code, en, sid)
        val = driver.find_element(By.ID, f"a_sick_{v}_{sv}").get_attribute("value")
        log(f"  [{mark}] {dx['code_raw']} {dx['name_en'][:32]}  → {val} ({how})")
        ok += 1

    log(f"진단명 입력 완료 ({ok}/{len(diagnoses)}건).")


# ============================================================
# 4. EMERGENCY ROOM (step=3)
# ============================================================
def fill_emergency_room(driver, patients, log=print):
    """03 페이지 EMERGENCY ROOM 채우기.
    명수 설정 후 행별: 등록번호/병실(ER 고정)/이름/성별/나이/입퇴원(퇴원 고정)
    """
    switch_to_step(driver, 3)
    n = len(patients)
    log(f"EMERGENCY ROOM 명수 {n}명 설정...")

    em = driver.find_element(By.ID, "emergency")
    driver.execute_script(
        "arguments[0].value=arguments[1];"
        "arguments[0].dispatchEvent(new Event('change'));",
        em, str(n))

    try:
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".emergency_tr")) >= n)
    except TimeoutException:
        cur = len(driver.find_elements(By.CSS_SELECTOR, ".emergency_tr"))
        raise RuntimeError(f"응급실 행 생성 실패 (기대 {n}, 현재 {cur})")

    for idx, p in enumerate(patients, start=1):
        row = driver.find_element(By.ID, f"emergency_{idx}")
        log(f"  [{idx}행] {p['regnum']} {p['name']} (ER/퇴원)")

        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='er_regnum[]']"), p["regnum"])
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='er_room[]']"), "ER")  # 병실 고정
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='er_name[]']"), p["name"])
        _set_text(row.find_element(By.CSS_SELECTOR, "input[name='er_age[]']"), p["age"])

        # 성별
        if p["sex"] == "M":
            driver.find_element(By.ID, f"er_sex_{idx}_1").click()
        elif p["sex"] == "F":
            driver.find_element(By.ID, f"er_sex_{idx}_2").click()

        # 입퇴원여부 = 퇴원(2) 고정
        Select(row.find_element(By.CSS_SELECTOR, "select[name='er_adm_dis[]']")).select_by_value("2")

    log("EMERGENCY ROOM 입력 완료.")


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== xls 파싱 테스트 ===")
    pts = parse_admission_xls(r"C:\Users\Administrator\Desktop\ps\입원목록.xls")
    for p in pts:
        print(p)

    print("\n=== 진단명 텍스트 파싱 테스트 ===")
    with open(r"C:\Users\Administrator\Desktop\ps\진단명.txt", encoding="utf-8") as f:
        dx = parse_diagnosis_text(f.read())
    for d in dx:
        print(d)
